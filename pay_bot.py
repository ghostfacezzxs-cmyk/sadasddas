import asyncio
import logging
from datetime import datetime
from io import BytesIO

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet
import os

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8632368659:AAGRt_xoW2F2K-JI_w1nJtS9WoujmR_EqWg")
ADMIN_ID = 8153647469

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Pending payments: {admin_msg_id: {user_id, username, amount, login, date}}
pending = {}


def generate_receipt_pdf(user_id: int, username: str, amount: int, login: str, receipt_id: str, date: str) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("<b>LanderShop</b>", styles['Title']))
    story.append(Paragraph("Чек об оплате", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1))
    story.append(Spacer(1, 0.3*cm))

    # Amount
    story.append(Paragraph(f"<b>Сумма: {amount} руб.</b>", styles['Heading1']))
    story.append(Paragraph("Пополнение баланса LanderShop", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1))
    story.append(Spacer(1, 0.3*cm))

    # Details
    data = [
        ["Номер чека:", receipt_id],
        ["Дата и время:", date],
        ["Telegram ID:", str(user_id)],
        ["Username:", f"@{username}" if username else "—"],
        ["Логин на сайте:", login],
        ["Сумма:", f"{amount} руб."],
        ["Статус:", "Ожидает подтверждения"],
    ]

    table = Table(data, colWidths=[5*cm, 11*cm])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.8*cm))

    story.append(Paragraph(
        "После подтверждения оплаты администратором баланс будет зачислен в течение 5 минут.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("LanderShop | @landershoping", styles['Normal']))

    doc.build(story)
    buf.seek(0)
    return buf


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в LanderShop!\n\n"
        "💰 Для пополнения баланса используйте команду:\n"
        "<code>/pay [сумма] [логин_на_сайте]</code>\n\n"
        "Пример: <code>/pay 500 ivan_petrov</code>\n\n"
        "После отправки команды вы получите чек, "
        "который будет отправлен администратору для подтверждения.",
        parse_mode="HTML"
    )


@dp.message(Command("pay"))
async def cmd_pay(message: Message):
    args = message.text.split()[1:]

    if len(args) < 2:
        await message.answer(
            "❌ Неверный формат.\n\n"
            "Используйте: <code>/pay [сумма] [логин_на_сайте]</code>\n"
            "Пример: <code>/pay 500 ivan_petrov</code>",
            parse_mode="HTML"
        )
        return

    try:
        amount = int(args[0])
    except ValueError:
        await message.answer("❌ Сумма должна быть числом. Пример: <code>/pay 500 ivan_petrov</code>", parse_mode="HTML")
        return

    if amount < 50:
        await message.answer("❌ Минимальная сумма пополнения: 50 ₽")
        return

    if amount > 50000:
        await message.answer("❌ Максимальная сумма пополнения: 50 000 ₽")
        return

    login = args[1]
    user_id = message.from_user.id
    username = message.from_user.username or ""
    date = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    receipt_id = f"LS-{user_id}-{int(datetime.now().timestamp())}"

    # Generate PDF
    await message.answer("⏳ Генерирую чек...")
    pdf_buf = generate_receipt_pdf(user_id, username, amount, login, receipt_id, date)

    # Send PDF to user
    await message.answer_document(
        document=("receipt.pdf", pdf_buf),
        caption=(
            f"✅ Чек сформирован!\n\n"
            f"💰 Сумма: <b>{amount} ₽</b>\n"
            f"👤 Логин: <b>{login}</b>\n"
            f"🔖 Номер: <code>{receipt_id}</code>\n\n"
            f"Чек отправлен администратору. "
            f"После подтверждения баланс будет зачислен в течение 5 минут."
        ),
        parse_mode="HTML"
    )

    # Send to admin with approve button
    pdf_buf.seek(0)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Принять", callback_data=f"approve:{receipt_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{receipt_id}"),
    ]])

    admin_msg = await bot.send_document(
        chat_id=ADMIN_ID,
        document=("receipt.pdf", pdf_buf),
        caption=(
            f"🔔 <b>Новый запрос на пополнение</b>\n\n"
            f"👤 Пользователь: @{username} (ID: <code>{user_id}</code>)\n"
            f"🌐 Логин на сайте: <b>{login}</b>\n"
            f"💰 Сумма: <b>{amount} ₽</b>\n"
            f"📅 Дата: {date}\n"
            f"🔖 Чек: <code>{receipt_id}</code>"
        ),
        parse_mode="HTML",
        reply_markup=kb
    )

    pending[receipt_id] = {
        "user_id": user_id,
        "username": username,
        "amount": amount,
        "login": login,
        "date": date,
        "admin_msg_id": admin_msg.message_id
    }


@dp.callback_query(F.data.startswith("approve:"))
async def approve_payment(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    receipt_id = callback.data.split(":", 1)[1]
    data = pending.get(receipt_id)

    if not data:
        await callback.answer("Заявка не найдена или уже обработана", show_alert=True)
        return

    # Notify user
    await bot.send_message(
        chat_id=data["user_id"],
        text=(
            f"✅ <b>Оплата подтверждена!</b>\n\n"
            f"💰 Сумма <b>{data['amount']} ₽</b> будет зачислена на аккаунт "
            f"<b>{data['login']}</b> в течение 5 минут.\n\n"
            f"🔖 Чек: <code>{receipt_id}</code>\n"
            f"Спасибо за пополнение! 🎉"
        ),
        parse_mode="HTML"
    )

    # Update admin message
    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n✅ <b>ПРИНЯТО</b> администратором",
        parse_mode="HTML",
        reply_markup=None
    )

    del pending[receipt_id]
    await callback.answer("✅ Пользователь уведомлён")


@dp.callback_query(F.data.startswith("reject:"))
async def reject_payment(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    receipt_id = callback.data.split(":", 1)[1]
    data = pending.get(receipt_id)

    if not data:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    await bot.send_message(
        chat_id=data["user_id"],
        text=(
            f"❌ <b>Оплата отклонена</b>\n\n"
            f"Ваш запрос на пополнение <b>{data['amount']} ₽</b> был отклонён.\n"
            f"Обратитесь в поддержку: @landershoping\n\n"
            f"🔖 Чек: <code>{receipt_id}</code>"
        ),
        parse_mode="HTML"
    )

    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n❌ <b>ОТКЛОНЕНО</b> администратором",
        parse_mode="HTML",
        reply_markup=None
    )

    del pending[receipt_id]
    await callback.answer("❌ Пользователь уведомлён об отклонении")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
