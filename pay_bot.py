import asyncio
import logging
from datetime import datetime
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8632368659:AAGRt_xoW2F2K-JI_w1nJtS9WoujmR_EqWg")
ADMIN_ID = 8153647469

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# pending[receipt_id] = {user_id, username, amount, login, date}
pending = {}


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в <b>LanderShop</b>!\n\n"
        "💰 Для пополнения баланса используйте команду:\n"
        "<code>/pay [сумма] [логин_на_сайте]</code>\n\n"
        "Пример: <code>/pay 500 ivan_petrov</code>\n\n"
        "После отправки команды чек будет отправлен администратору для подтверждения.",
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
        await message.answer(
            "❌ Сумма должна быть числом.\n"
            "Пример: <code>/pay 500 ivan_petrov</code>",
            parse_mode="HTML"
        )
        return

    if amount < 50:
        await message.answer("❌ Минимальная сумма пополнения: <b>50 ₽</b>", parse_mode="HTML")
        return

    if amount > 50000:
        await message.answer("❌ Максимальная сумма пополнения: <b>50 000 ₽</b>", parse_mode="HTML")
        return

    login = args[1]
    user_id = message.from_user.id
    username = message.from_user.username or "нет"
    date = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    receipt_id = f"LS-{user_id}-{int(datetime.now().timestamp())}"

    # Чек для пользователя
    receipt_text = (
        f"🧾 <b>ЧЕК ОПЛАТЫ — LanderShop</b>\n"
        f"{'─' * 30}\n"
        f"🔖 Номер: <code>{receipt_id}</code>\n"
        f"📅 Дата: {date}\n"
        f"{'─' * 30}\n"
        f"👤 Telegram: @{username} (<code>{user_id}</code>)\n"
        f"🌐 Логин на сайте: <b>{login}</b>\n"
        f"💰 Сумма: <b>{amount} ₽</b>\n"
        f"📋 Назначение: Пополнение баланса\n"
        f"{'─' * 30}\n"
        f"💳 Реквизиты для оплаты:\n"
        f"<b>5599 0021 3662 7033</b>\n"
        f"{'─' * 30}\n"
        f"После оплаты отправьте скриншот в @landershoping\n"
        f"Баланс будет зачислен в течение <b>5 минут</b> после подтверждения.\n"
        f"⏳ Статус: <b>Ожидает оплаты</b>"
    )

    await message.answer(receipt_text, parse_mode="HTML")

    # Чек для администратора
    admin_text = (
        f"🔔 <b>НОВЫЙ ЗАПРОС НА ПОПОЛНЕНИЕ</b>\n"
        f"{'─' * 30}\n"
        f"🔖 Чек: <code>{receipt_id}</code>\n"
        f"📅 Дата: {date}\n"
        f"{'─' * 30}\n"
        f"👤 @{username} (ID: <code>{user_id}</code>)\n"
        f"🌐 Логин: <b>{login}</b>\n"
        f"💰 Сумма: <b>{amount} ₽</b>\n"
        f"{'─' * 30}\n"
        f"Нажми кнопку для подтверждения или отклонения:"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Принять", callback_data=f"approve:{receipt_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{receipt_id}"),
    ]])

    await bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text,
        parse_mode="HTML",
        reply_markup=kb
    )

    pending[receipt_id] = {
        "user_id": user_id,
        "username": username,
        "amount": amount,
        "login": login,
        "date": date,
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

    await bot.send_message(
        chat_id=data["user_id"],
        text=(
            f"✅ <b>Оплата подтверждена!</b>\n\n"
            f"💰 Сумма <b>{data['amount']} ₽</b> будет зачислена на аккаунт "
            f"<b>{data['login']}</b> в течение <b>5 минут</b>.\n\n"
            f"🔖 Чек: <code>{receipt_id}</code>\n\n"
            f"Спасибо за пополнение! 🎉"
        ),
        parse_mode="HTML"
    )

    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ <b>ПРИНЯТО</b>",
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

    await callback.message.edit_text(
        callback.message.text + f"\n\n❌ <b>ОТКЛОНЕНО</b>",
        parse_mode="HTML",
        reply_markup=None
    )

    del pending[receipt_id]
    await callback.answer("❌ Пользователь уведомлён")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
