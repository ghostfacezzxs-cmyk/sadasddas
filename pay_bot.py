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
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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
    title_style = ParagraphStyle('title', fontSize=22, fontName='Helvetica-Bold',
                                  alignment=TA_CENTER, textColor=colors.HexColor('#7c3aed'),
                                  spaceAfter=6)
    sub_style = ParagraphStyle('sub', fontSize=11, fontName='Helvetica',
                                alignment=TA_CENTER, textColor=colors.HexColor('#6b7280'),
                                spaceAfter=20)
    label_style = ParagraphStyle('label', fontSize=10, fontName='Helvetica',
                                  textColor=colors.HexColor('#6b7280'))
    value_style = ParagraphStyle('value', fontSize=12, fontName='Helvetica-Bold',
                                  textColor=colors.HexColor('#111827'))
    amount_style = ParagraphStyle('amount', fontSize=28, fontName='Helvetica-Bold',
                                   alignment=TA_CENTER, textColor=colors.HexColor('#7c3aed'),
                                   spaceBefore=10, spaceAfter=10)
    footer_style = ParagraphStyle('footer', fontSize=9, fontName='Helvetica',
                                   alignment=TA_CENTER, textColor=colors.HexColor('#9ca3af'))

    story = []

    # Header
    story.append(Paragraph("LanderShop", title_style))
    story.append(Paragraph("Чек об оплате / Payment Receipt", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
    story.append(Spacer(1, 0.5*cm))

    # Amount
    story.append(Paragraph(f"{amount} ₽", amount_style))
    story.append(Paragraph("Пополнение баланса", ParagraphStyle('c', fontSize=12,
                alignment=TA_CENTER, textColor=colors.HexColor('#6b7280'), spaceAfter=20)))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
    story.append(Spacer(1, 0.4*cm))

    # Details table
    data = [
        [Paragraph("Номер чека", label_style), Paragraph(receipt_id, value_style)],
        [Paragraph("Дата и время", label_style), Paragraph(date, value_style)],
        [Paragraph("Telegram ID", label_style), Paragraph(str(user_id), value_style)],
        [Paragraph("Username", label_style), Paragraph(f"@{username}" if username else "—", value_style)],
        [Paragraph("Логин на сайте", label_style), Paragraph(login, value_style)],
        [Paragraph("Сумма", label_style), Paragraph(f"{amount} ₽", value_style)],
        [Paragraph("Статус", label_style), Paragraph("⏳ Ожидает подтверждения", value_style)],
    ]

    table = Table(data, colWidths=[5*cm, 11*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f9fafb'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.8*cm))

    # Info box
    info_style = ParagraphStyle('info', fontSize=10, fontName='Helvetica',
                                 textColor=colors.HexColor('#374151'),
                                 backColor=colors.HexColor('#f3f4f6'),
                                 borderPad=10, spaceAfter=20)
    story.append(Paragraph(
        "После подтверждения оплаты администратором баланс будет зачислен "
        "в течение 5 минут. По вопросам: @landershoping",
        info_style
    ))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("LanderShop — Моды и скрипты для SA-MP", footer_style))
    story.append(Paragraph(f"landershop.ru | @landershoping", footer_style))

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
