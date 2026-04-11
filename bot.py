# -*- coding: utf-8 -*-
import asyncio, random, string, time
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8323808452:AAFRAd_m4g_mfgDe8r2AqSkckcjZLBFnrtw"
FOUNDER_ID = 8153647469
PROMOTE_THRESHOLD = 500
ADMIN_CHAT = -1003922088877
SUPPORT_CHAT = -1003940798566
PUB_PRICE = 5000
FREE_PUBS = 3

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

users = {}
listings = []
reports = []
support_msgs = []
admin_keys = {}
promote_requests = {}
orders = {}
pub_orders = {}

def gen_order_id():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

ROLES = {"player": "\u0418\u0433\u0440\u043e\u043a", "support": "\u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430", "admin": "\u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440", "founder": "\u041e\u0441\u043d\u043e\u0432\u0430\u0442\u0435\u043b\u044c"}
MAX_LISTINGS = 999999
LISTING_COOLDOWN = 1800

B_SELL = "\U0001F4E6 \u041f\u0440\u043e\u0434\u0430\u0442\u044c \u0432\u0435\u0449\u044c"
B_VIEW = "\U0001F6D2 \u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440 \u043f\u0440\u043e\u0434\u0430\u0436"
B_REP  = "\U0001F6A8 \u0420\u0435\u043f\u043e\u0440\u0442"
B_SUP  = "\U0001F4AC \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430"
B_PRO  = "\U0001F464 \u041f\u0440\u043e\u0444\u0438\u043b\u044c"
B_PAN  = "\U0001F527 \u041f\u0430\u043d\u0435\u043b\u044c"
B_MY   = "\U0001F4CB \u041c\u043e\u0438 \u043e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u044f"
B_HELP = "\u2753 \u041f\u043e\u043c\u043e\u0449\u044c"

def get_user(uid, username=""):
    if uid not in users:
        users[uid] = {"role": "player", "username": username, "listings_count": 0,
                      "listings_reset_time": 0, "banned": False, "pub_banned_until": 0,
                      "support_answers": 0, "free_pubs": FREE_PUBS, "extra_pubs": 0,
                      "report_times": [], "support_times": []}
    if username:
        users[uid]["username"] = username
    return users[uid]

def get_pub_balance(uid):
    u = users.get(uid, {})
    return u.get("free_pubs", 0) + u.get("extra_pubs", 0)

def use_pub(uid):
    u = users[uid]
    if u.get("free_pubs", 0) > 0:
        u["free_pubs"] -= 1
    elif u.get("extra_pubs", 0) > 0:
        u["extra_pubs"] -= 1

def gen_key():
    return "".join(random.choices(string.digits, k=7))

def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=B_SELL), KeyboardButton(text=B_VIEW)],
        [KeyboardButton(text=B_MY),   KeyboardButton(text=B_REP)],
        [KeyboardButton(text=B_SUP),  KeyboardButton(text=B_HELP)],
        [KeyboardButton(text=B_PRO),  KeyboardButton(text=B_PAN)],
    ], resize_keyboard=True)

class S(StatesGroup):
    photo = State()
    item_name = State()
    item_price = State()
    description = State()
    report = State()
    support = State()
    auth = State()
    assign_role = State()
    assign_user = State()
    reply_report = State()
    reply_support = State()
    buy_amount = State()
    buy_screenshot = State()
    buy_pubs_qty = State()
    buy_pubs_screenshot = State()

@dp.message(Command("start"))
async def cmd_start(msg: types.Message, state: FSMContext):
    if msg.chat.type != "private": return
    await state.clear()
    uid = msg.from_user.id
    uname = msg.from_user.username or str(uid)
    u = get_user(uid, uname)
    if uid == FOUNDER_ID:
        u["role"] = "founder"
    args = msg.text.split()
    if len(args) > 1:
        param = args[1]
        if param.startswith("reply_report_"):
            rid = int(param.split("_")[-1])
            if users.get(uid, {}).get("role") in ("admin", "founder"):
                await state.update_data(reply_id=rid)
                await msg.answer(f"\u041e\u0442\u0432\u0435\u0442 \u043d\u0430 \u0440\u0435\u043f\u043e\u0440\u0442 #{rid}:")
                await state.set_state(S.reply_report)
                return
        elif param.startswith("reply_support_"):
            sid = int(param.split("_")[-1])
            if users.get(uid, {}).get("role") in ("support", "admin", "founder"):
                await state.update_data(reply_id=sid)
                await msg.answer(f"\u041e\u0442\u0432\u0435\u0442 \u043d\u0430 \u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0435 #{sid}:")
                await state.set_state(S.reply_support)
                return
    await msg.answer(f"\u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c, @{uname}!\n\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435:", reply_markup=main_kb())

@dp.message(Command("cancel"))
async def cmd_cancel(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("\u041e\u0442\u043c\u0435\u043d\u0435\u043d\u043e.", reply_markup=main_kb())

@dp.message(F.text == B_PRO)
async def profile(msg: types.Message):
    uid = msg.from_user.id
    u = get_user(uid)
    now = time.time()
    pub = u.get("pub_banned_until", 0)
    pub_s = f"\u0417\u0430\u043f\u0440\u0435\u0442 {int((pub-now)/60)} \u043c\u0438\u043d" if pub > now else "\u0410\u043a\u0442\u0438\u0432\u0435\u043d"
    ban_s = "\u0417\u0430\u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u0430\u043d" if u.get("banned") else "\u0410\u043a\u0442\u0438\u0432\u0435\u043d"
    pubs = get_pub_balance(uid)
    await msg.answer(
        f"\U0001F464 \u041f\u0440\u043e\u0444\u0438\u043b\u044c\n\n"
        f"\U0001F3F7 @{u['username']}\n"
        f"\u2B50 {ROLES[u['role']]}\n"
        f"\U0001F4E6 \u041f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0439: {pubs}\n"
        f"\U0001F512 \u0410\u043a\u043a\u0430\u0443\u043d\u0442: {ban_s}\n"
        f"\U0001F4DD \u041f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438: {pub_s}"
    )

@dp.message(F.text == B_SELL)
async def sell_start(msg: types.Message, state: FSMContext):
    await state.clear()
    uid = msg.from_user.id
    u = get_user(uid)
    if u.get("banned"): return await msg.answer("\u0412\u044b \u0437\u0430\u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u0430\u043d\u044b.")
    now = time.time()
    if u.get("pub_banned_until", 0) > now:
        return await msg.answer(f"\u0417\u0430\u043f\u0440\u0435\u0442 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0439. \u041e\u0441\u0442\u0430\u043b\u043e\u0441\u044c {int((u['pub_banned_until']-now)/60)} \u043c\u0438\u043d.")
    pubs = get_pub_balance(uid)
    if pubs <= 0:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="\U0001F6D2 \u041a\u0443\u043f\u0438\u0442\u044c", callback_data="buy_pubs"),
            InlineKeyboardButton(text="\u2B05 \u041d\u0430\u0437\u0430\u0434", callback_data="back_main")
        ]])
        return await msg.answer(
            "\u0412\u0430\u0448\u0438 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438 \u0437\u0430\u043a\u043e\u043d\u0447\u0438\u043b\u0438\u0441\u044c\n\n"
            "\u0427\u0442\u043e\u0431\u044b \u043a\u0443\u043f\u0438\u0442\u044c \u0435\u0449\u0435 \u043d\u0430\u0436\u043c\u0438\u0442\u0435 \u043d\u0430 \u043a\u043d\u043e\u043f\u043a\u0443 \u043d\u0438\u0436\u0435",
            reply_markup=kb)
    await msg.answer("\U0001F4F8 \u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0444\u043e\u0442\u043e \u0432\u0430\u0448\u0435\u0439 \u0432\u0435\u0449\u0438:")
    await state.set_state(S.photo)

@dp.callback_query(F.data == "back_main")
async def back_main(call: types.CallbackQuery):
    await call.message.answer("\u0413\u043b\u0430\u0432\u043d\u043e\u0435 \u043c\u0435\u043d\u044e:", reply_markup=main_kb())
    await call.answer()

@dp.callback_query(F.data == "buy_pubs")
async def buy_pubs_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(
        "\U0001F4E6 \u041f\u043e\u043a\u0443\u043f\u043a\u0430 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0439\n\n"
        f"\U0001F4B0 \u0426\u0435\u043d\u0430: {PUB_PRICE:,} \u0437\u0430 1 \u0448\u0442\n\n"
        "\u0421\u043a\u043e\u043b\u044c\u043a\u043e \u0436\u0435\u043b\u0430\u0435\u0442\u0435 \u043f\u0440\u0438\u043e\u0431\u0440\u0435\u0441\u0442\u0438? (\u043c\u0438\u043d 1, \u043c\u0430\u043a\u0441 10):"
    )
    await state.set_state(S.buy_pubs_qty)
    await call.answer()

@dp.message(S.buy_pubs_qty, F.text)
async def buy_pubs_qty(msg: types.Message, state: FSMContext):
    try:
        qty = int(msg.text.strip())
        if qty < 1 or qty > 10: raise ValueError
    except:
        return await msg.answer("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0447\u0438\u0441\u043b\u043e \u043e\u0442 1 \u0434\u043e 10.")
    total = qty * PUB_PRICE
    await state.update_data(buy_pubs_qty=qty, buy_pubs_total=total)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="\u2705 \u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c", callback_data="confirm_pubs_buy"),
        InlineKeyboardButton(text="\u274C \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="back_main")
    ]])
    await msg.answer(
        f"\U0001F4E6 \u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e: {qty} \u0448\u0442\n"
        f"\U0001F4B0 \u0421\u0442\u043e\u0438\u043c\u043e\u0441\u0442\u044c: {total:,} \u0432\u0430\u043b\u044e\u0442\u044b\n\n"
        "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u0435 \u043f\u043e\u043a\u0443\u043f\u043a\u0443:",
        reply_markup=kb)

@dp.callback_query(F.data == "confirm_pubs_buy")
async def confirm_pubs_buy(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    total = data.get("buy_pubs_total", 0)
    await call.message.answer(
        f"\U0001F4B3 \u041f\u0440\u043e\u0438\u0437\u0432\u0435\u0434\u0438\u0442\u0435 \u043e\u043f\u043b\u0430\u0442\u0443 {total:,} \u043d\u0430 ID: 1892508\n\n"
        "\u041f\u043e\u0441\u043b\u0435 \u043e\u043f\u043b\u0430\u0442\u044b \u043f\u0440\u0438\u0448\u043b\u0438\u0442\u0435 \u0441\u043a\u0440\u0438\u043d\u0448\u043e\u0442 \u043e\u043f\u043b\u0430\u0442\u044b:"
    )
    await state.set_state(S.buy_pubs_screenshot)
    await call.answer()

@dp.message(S.buy_pubs_screenshot, F.photo)
async def buy_pubs_screenshot(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = msg.from_user.id
    uname = msg.from_user.username or str(uid)
    qty = data.get("buy_pubs_qty", 1)
    total = data.get("buy_pubs_total", 0)
    order_id = gen_order_id()
    pub_orders[order_id] = {"buyer_id": uid, "buyer_username": uname, "qty": qty, "amount": total, "status": "pending"}
    await state.clear()
    await msg.answer(f"\u2705 \u041e\u0436\u0438\u0434\u0430\u0439\u0442\u0435 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f \u043e\u043f\u043b\u0430\u0442\u044b.\n\u0415\u0441\u043b\u0438 \u0432\u0441\u0435 \u0445\u043e\u0440\u043e\u0448\u043e \u0432\u0430\u043c \u0432\u044b\u0434\u0430\u0434\u0443\u0442 \u0432\u0430\u0448\u0438 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438.")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="\u2705 \u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c", callback_data=f"confirm_pub_{order_id}"),
        InlineKeyboardButton(text="\u274C \u041e\u0442\u043a\u043b\u043e\u043d\u0438\u0442\u044c", callback_data=f"reject_pub_{order_id}")
    ]])
    try:
        await bot.send_photo(FOUNDER_ID, msg.photo[-1].file_id,
            caption=f"\U0001F4E6 \u041e\u043f\u043b\u0430\u0442\u0430 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0439\n\n"
                    f"\U0001F464 @{uname}\n"
                    f"\U0001F4E6 \u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e: {qty} \u0448\u0442\n"
                    f"\U0001F4B0 \u0421\u0443\u043c\u043c\u0430: {total:,}",
            reply_markup=kb)
    except: pass

@dp.callback_query(F.data.startswith("confirm_pub_"))
async def confirm_pub(call: types.CallbackQuery):
    if call.from_user.id != FOUNDER_ID: return await call.answer()
    order_id = call.data.replace("confirm_pub_", "")
    order = pub_orders.get(order_id)
    if not order: return await call.answer()
    order["status"] = "confirmed"
    uid = order["buyer_id"]
    qty = order["qty"]
    if uid in users:
        users[uid]["extra_pubs"] = users[uid].get("extra_pubs", 0) + qty
    try:
        await bot.send_message(uid, f"\u2705 \u041e\u043f\u043b\u0430\u0442\u0430 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0430!\n\U0001F4E6 \u0412\u0430\u043c \u0432\u044b\u0434\u0430\u043d\u043e {qty} \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0439.")
    except: pass
    await call.message.edit_caption(caption=call.message.caption + "\n\n\u2705 \u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u043e")
    await call.answer()

@dp.callback_query(F.data.startswith("reject_pub_"))
async def reject_pub(call: types.CallbackQuery):
    if call.from_user.id != FOUNDER_ID: return await call.answer()
    order_id = call.data.replace("reject_pub_", "")
    order = pub_orders.get(order_id)
    if not order: return await call.answer()
    order["status"] = "rejected"
    try:
        await bot.send_message(order["buyer_id"], "\u274C \u041e\u043f\u043b\u0430\u0442\u0430 \u043e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u0430.")
    except: pass
    await call.message.edit_caption(caption=call.message.caption + "\n\n\u274C \u041e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u043e")
    await call.answer()

@dp.message(S.photo, F.photo)
async def sell_photo(msg: types.Message, state: FSMContext):
    await state.update_data(photo_id=msg.photo[-1].file_id)
    await msg.answer("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0432\u0435\u0449\u0438 (\u043f\u0440\u0438\u043c\u0435\u0440: \u0425\u0443\u0434\u0438 \u0410\u043d\u0442\u0438 \u0425\u0430\u0439\u043f):")
    await state.set_state(S.item_name)

@dp.message(S.item_name, F.text)
async def sell_item_name(msg: types.Message, state: FSMContext):
    await state.update_data(item_name=msg.text)
    await msg.answer("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0446\u0435\u043d\u0443 (\u043f\u0440\u0438\u043c\u0435\u0440: 1500000):")
    await state.set_state(S.item_price)

@dp.message(S.item_price, F.text)
async def sell_item_price(msg: types.Message, state: FSMContext):
    await state.update_data(item_price=msg.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="\u0414\u0430", callback_data="desc_yes"),
        InlineKeyboardButton(text="\u041d\u0435\u0442", callback_data="desc_no")
    ]])
    await msg.answer("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435?", reply_markup=kb)

@dp.callback_query(F.data == "desc_yes")
async def desc_yes(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("\u041d\u0430\u043f\u0438\u0448\u0438\u0442\u0435 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435:")
    await state.set_state(S.description)
    await call.answer()

@dp.callback_query(F.data == "desc_no")
async def desc_no(call: types.CallbackQuery, state: FSMContext):
    await finish_listing(call.message, state, call.from_user)
    await call.answer()

@dp.message(S.description, F.text)
async def sell_desc(msg: types.Message, state: FSMContext):
    await state.update_data(description=msg.text)
    await finish_listing(msg, state, msg.from_user)

async def finish_listing(msg, state, user):
    data = await state.get_data()
    uid = user.id
    uname = user.username or str(uid)
    u = get_user(uid, uname)
    use_pub(uid)
    order_id = gen_order_id()
    item_name = data.get("item_name", "")
    item_price = data.get("item_price", "")
    description = data.get("description", "")
    full_desc = f"{item_name}\n\u0426\u0435\u043d\u0430: {item_price}"
    if description:
        full_desc += f"\n{description}"
    listings.append({"id": len(listings)+1, "user_id": uid, "username": uname,
                     "photo_id": data.get("photo_id"),
                     "item_name": item_name.lower(),
                     "item_price": item_price,
                     "description": full_desc,
                     "time": time.time(), "order_id": order_id})
    await state.clear()
    await msg.answer(f"\u2705 \u041e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u0435 \u043e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d\u043e!\n\U0001F4CB \u0417\u0430\u043a\u0430\u0437: #{order_id}", reply_markup=main_kb())

@dp.message(F.text == B_VIEW)
async def view_listings(msg: types.Message):
    await show_listing(msg, msg.from_user.id, 0)

async def show_listing(msg, uid, index):
    ul = [l for l in listings if l["user_id"] != uid]
    if not ul or index >= len(ul):
        return await msg.answer("\u041e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u044f \u0437\u0430\u043a\u043e\u043d\u0447\u0438\u043b\u0438\u0441\u044c \u2014 \u043e\u0436\u0438\u0434\u0430\u0439\u0442\u0435 \u0434\u0440\u0443\u0433\u0438\u0445 \u043e\u0442 \u0438\u0433\u0440\u043e\u043a\u043e\u0432.")
    l = ul[index]
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0435\u0435", callback_data=f"next_{index+1}_{uid}"),
        InlineKeyboardButton(text="\U0001F6D2 \u041a\u0443\u043f\u0438\u0442\u044c", callback_data=f"buy_{l['id']}")
    ]])
    order_id = l.get("order_id", "??????")
    await msg.answer_photo(l["photo_id"], caption=f"\U0001F4DD {l['description']}\n\n\U0001F4CB \u0417\u0430\u043a\u0430\u0437 #{order_id}", reply_markup=kb)

@dp.callback_query(F.data.startswith("next_"))
async def next_listing(call: types.CallbackQuery):
    _, idx, uid = call.data.split("_")
    await show_listing(call.message, int(uid), int(idx))
    await call.answer()

@dp.message(F.text == B_MY)
async def my_listings(msg: types.Message):
    await show_my_listing(msg, msg.from_user.id, 0)

async def show_my_listing(msg, uid, index):
    ul = [l for l in listings if l["user_id"] == uid]
    if not ul:
        return await msg.answer("\u0423 \u0432\u0430\u0441 \u043d\u0435\u0442 \u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0445 \u043e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u0439.")
    if index >= len(ul):
        return await msg.answer("\u0411\u043e\u043b\u044c\u0448\u0435 \u043e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u0439 \u043d\u0435\u0442.")
    l = ul[index]
    buttons = []
    if index + 1 < len(ul):
        buttons.append(InlineKeyboardButton(text="\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0435\u0435", callback_data=f"my_next_{index+1}_{uid}"))
    buttons.append(InlineKeyboardButton(text="\u274C \u0423\u0434\u0430\u043b\u0438\u0442\u044c", callback_data=f"del_listing_{l['id']}"))
    kb = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await msg.answer_photo(l["photo_id"], caption=f"\U0001F4CB #{l.get('order_id','?')}\n{l['description']}\n\n{index+1}/{len(ul)}", reply_markup=kb)

@dp.callback_query(F.data.startswith("my_next_"))
async def my_next(call: types.CallbackQuery):
    _, _, idx, uid = call.data.split("_")
    await show_my_listing(call.message, int(uid), int(idx))
    await call.answer()

@dp.callback_query(F.data.startswith("del_listing_"))
async def del_listing(call: types.CallbackQuery):
    lid = int(call.data.split("_")[-1])
    uid = call.from_user.id
    listing = next((l for l in listings if l["id"] == lid and l["user_id"] == uid), None)
    if listing:
        listings.remove(listing)
        await call.message.edit_caption(caption="\u274C \u041e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u0435 \u0443\u0434\u0430\u043b\u0435\u043d\u043e.")
    await call.answer()

@dp.message(F.text == B_REP)
async def report_start(msg: types.Message, state: FSMContext):
    await state.clear()
    if get_user(msg.from_user.id).get("banned"): return await msg.answer("\u0412\u044b \u0437\u0430\u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u0430\u043d\u044b.")
    await msg.answer("\u041e\u043f\u0438\u0448\u0438\u0442\u0435 \u043f\u0440\u043e\u0431\u043b\u0435\u043c\u0443:")
    await state.set_state(S.report)

@dp.message(S.report, F.text)
async def report_text(msg: types.Message, state: FSMContext):
    uid = msg.from_user.id
    uname = msg.from_user.username or str(uid)
    u = get_user(uid, uname)
    now = time.time()
    u["report_times"] = [t for t in u.get("report_times", []) if now - t < 600]
    if len(u["report_times"]) >= 2:
        await state.clear()
        return await msg.answer("\u0421\u043b\u0438\u0448\u043a\u043e\u043c \u043c\u043d\u043e\u0433\u043e \u0440\u0435\u043f\u043e\u0440\u0442\u043e\u0432. \u041f\u043e\u0434\u043e\u0436\u0434\u0438\u0442\u0435 10 \u043c\u0438\u043d.")
    u["report_times"].append(now)
    rid = len(reports) + 1
    reports.append({"id": rid, "from_id": uid, "from_username": uname, "text": msg.text, "answered": False})
    await state.clear()
    await msg.answer("\u0420\u0435\u043f\u043e\u0440\u0442 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d!", reply_markup=main_kb())
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="\u2709\uFE0F \u041e\u0442\u0432\u0435\u0442\u0438\u0442\u044c", url=f"https://t.me/{{(await bot.get_me()).username}}?start=reply_report_{rid}")
    ]])
    try:
        await bot.send_message(ADMIN_CHAT, f"\U0001F6A8 \u0420\u0435\u043f\u043e\u0440\u0442 #{rid}\n\U0001F464 @{uname}\n\U0001F4DD {msg.text}", reply_markup=kb)
    except: pass

@dp.message(F.text == B_SUP)
async def support_start(msg: types.Message, state: FSMContext):
    await state.clear()
    if get_user(msg.from_user.id).get("banned"): return await msg.answer("\u0412\u044b \u0437\u0430\u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u0430\u043d\u044b.")
    await msg.answer("\u041d\u0430\u043f\u0438\u0448\u0438\u0442\u0435 \u0432\u043e\u043f\u0440\u043e\u0441:")
    await state.set_state(S.support)

@dp.message(S.support, F.text)
async def support_text(msg: types.Message, state: FSMContext):
    uid = msg.from_user.id
    uname = msg.from_user.username or str(uid)
    u = get_user(uid, uname)
    now = time.time()
    u["support_times"] = [t for t in u.get("support_times", []) if now - t < 600]
    if len(u["support_times"]) >= 2:
        await state.clear()
        return await msg.answer("\u0421\u043b\u0438\u0448\u043a\u043e\u043c \u043c\u043d\u043e\u0433\u043e \u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0439. \u041f\u043e\u0434\u043e\u0436\u0434\u0438\u0442\u0435 10 \u043c\u0438\u043d.")
    u["support_times"].append(now)
    sid = len(support_msgs) + 1
    support_msgs.append({"id": sid, "from_id": uid, "from_username": uname, "text": msg.text, "answered": False})
    await state.clear()
    await msg.answer("\u041e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e \u0432 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0443!", reply_markup=main_kb())
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="\u2709\uFE0F \u041e\u0442\u0432\u0435\u0442\u0438\u0442\u044c", url=f"https://t.me/{{(await bot.get_me()).username}}?start=reply_support_{sid}")
    ]])
    try:
        await bot.send_message(SUPPORT_CHAT, f"\U0001F4AC \u041e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0435 #{sid}\n\U0001F464 @{uname}\n\U0001F4DD {msg.text}", reply_markup=kb)
    except: pass

@dp.message(F.text == B_HELP)
async def help_cmd(msg: types.Message):
    await msg.answer(
        "\u2753 \u041f\u043e\u043c\u043e\u0449\u044c\n\n"
        "\U0001F4E6 \u041f\u0440\u043e\u0434\u0430\u0442\u044c \u0432\u0435\u0449\u044c \u2014 \u043e\u043f\u0443\u0431\u043b\u0438\u043a\u0443\u0439\u0442\u0435 \u043e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u0435 \u0441 \u0444\u043e\u0442\u043e. \u0411\u0435\u0441\u043f\u043b\u0430\u0442\u043d\u043e: 3 \u0448\u0442, \u0434\u0430\u043b\u0435\u0435 \u043f\u043b\u0430\u0442\u043d\u043e.\n\n"
        "\U0001F6D2 \u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440 \u043f\u0440\u043e\u0434\u0430\u0436 \u2014 \u043f\u0440\u043e\u0441\u043c\u0430\u0442\u0440\u0438\u0432\u0430\u0439\u0442\u0435 \u043e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u044f. \u041a\u043d\u043e\u043f\u043a\u0430 \u041a\u0443\u043f\u0438\u0442\u044c \u2014 \u0432\u043d\u0435\u0441\u0442\u0438 \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u044e 7%.\n\n"
        "\U0001F4CB \u041c\u043e\u0438 \u043e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u044f \u2014 \u0441\u043c\u043e\u0442\u0440\u0438\u0442\u0435 \u0438 \u0443\u0434\u0430\u043b\u044f\u0439\u0442\u0435 \u0441\u0432\u043e\u0438 \u043e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u044f.\n\n"
        "\U0001F6A8 \u0420\u0435\u043f\u043e\u0440\u0442 \u2014 \u0435\u0441\u043b\u0438 \u0438\u0433\u0440\u043e\u043a \u043d\u0430\u0440\u0443\u0448\u0430\u0435\u0442 \u043f\u0440\u0430\u0432\u0438\u043b\u0430. \u041b\u0438\u043c\u0438\u0442: 2 \u0440\u0435\u043f\u043e\u0440\u0442\u0430 \u0432 10 \u043c\u0438\u043d.\n\n"
        "\U0001F4AC \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430 \u2014 \u0432\u043e\u043f\u0440\u043e\u0441\u044b \u043f\u043e \u0440\u0430\u0431\u043e\u0442\u0435 \u0431\u043e\u0442\u0430. \u041b\u0438\u043c\u0438\u0442: 2 \u0432 10 \u043c\u0438\u043d.\n\n"
        "/find #XXXXXX \u2014 \u043d\u0430\u0439\u0442\u0438 \u0437\u0430\u043a\u0430\u0437."
    )

@dp.callback_query(F.data.startswith("buy_"))
async def buy_start(call: types.CallbackQuery, state: FSMContext):
    lid = int(call.data.split("_")[1])
    listing = next((l for l in listings if l["id"] == lid), None)
    if not listing: return await call.answer("\u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e.")
    await state.update_data(buy_listing_id=lid)
    await call.message.answer("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u0443\u043c\u043c\u0443 \u0441\u0434\u0435\u043b\u043a\u0438 (\u0432 \u0432\u0430\u043b\u044e\u0442\u0435):")
    await state.set_state(S.buy_amount)
    await call.answer()

@dp.message(S.buy_amount, F.text)
async def buy_amount_handler(msg: types.Message, state: FSMContext):
    try:
        amount = float(msg.text.replace(" ", "").replace(",", "."))
    except:
        return await msg.answer("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0447\u0438\u0441\u043b\u043e.")
    commission = round(amount * 0.07)
    await state.update_data(buy_amount=amount, buy_commission=commission)
    await msg.answer(
        f"\U0001F4B0 \u0421\u0443\u043c\u043c\u0430: {int(amount):,}\n"
        f"\U0001F4B3 \u041a\u043e\u043c\u0438\u0441\u0441\u0438\u044f (7%): {commission:,}\n\n"
        f"\u041f\u0435\u0440\u0435\u0432\u0435\u0434\u0438\u0442\u0435 {commission:,} \u043d\u0430 ID: 1892508\n\n"
        "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0441\u043a\u0440\u0438\u043d\u0448\u043e\u0442 \u043e\u043f\u043b\u0430\u0442\u044b:"
    )
    await state.set_state(S.buy_screenshot)

@dp.message(S.buy_screenshot, F.photo)
async def buy_screenshot_handler(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = msg.from_user.id
    uname = msg.from_user.username or str(uid)
    lid = data["buy_listing_id"]
    amount = data["buy_amount"]
    commission = data["buy_commission"]
    listing = next((l for l in listings if l["id"] == lid), None)
    if not listing:
        await state.clear()
        return await msg.answer("\u041e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u0435 \u0431\u043e\u043b\u044c\u0448\u0435 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e.")
    order_id = gen_order_id()
    orders[order_id] = {"listing_id": lid, "buyer_id": uid, "buyer_username": uname,
                        "seller_id": listing["user_id"], "seller_username": listing["username"],
                        "amount": amount, "commission": commission, "status": "pending"}
    await state.clear()
    await msg.answer(f"\u2705 \u041e\u0436\u0438\u0434\u0430\u0439\u0442\u0435 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f.\n\U0001F4CB \u0417\u0430\u043a\u0430\u0437: #{order_id}")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="\u2705 \u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c", callback_data=f"confirm_order_{order_id}"),
        InlineKeyboardButton(text="\u274C \u041e\u0442\u043a\u043b\u043e\u043d\u0438\u0442\u044c", callback_data=f"reject_order_{order_id}")
    ]])
    try:
        await bot.send_photo(FOUNDER_ID, msg.photo[-1].file_id,
            caption=f"\U0001F4B0 \u041d\u043e\u0432\u0430\u044f \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u044f\n\n"
                    f"\U0001F464 \u041f\u043e\u043a\u0443\u043f\u0430\u0442\u0435\u043b\u044c: @{uname}\n"
                    f"\U0001F4CB \u0417\u0430\u043a\u0430\u0437: #{order_id}\n"
                    f"\U0001F4B0 \u0421\u0443\u043c\u043c\u0430: {int(amount):,}\n"
                    f"\U0001F4B3 \u041a\u043e\u043c\u0438\u0441\u0441\u0438\u044f: {commission:,}",
            reply_markup=kb)
    except: pass

@dp.callback_query(F.data.startswith("confirm_order_"))
async def confirm_order(call: types.CallbackQuery):
    if call.from_user.id != FOUNDER_ID: return await call.answer()
    order_id = call.data.replace("confirm_order_", "")
    order = orders.get(order_id)
    if not order: return await call.answer()
    order["status"] = "confirmed"
    try:
        await bot.send_message(order["buyer_id"],
            f"\u2705 \u041a\u043e\u043c\u0438\u0441\u0441\u0438\u044f \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0430!\n\n"
            f"\U0001F464 \u041f\u0440\u043e\u0434\u0430\u0432\u0435\u0446: @{order['seller_username']}\n"
            f"\U0001F4CB \u0417\u0430\u043a\u0430\u0437: #{order_id}\n\n"
            "\u0421\u0432\u044f\u0436\u0438\u0442\u0435\u0441\u044c \u0441 \u043f\u0440\u043e\u0434\u0430\u0432\u0446\u043e\u043c.")
    except: pass
    await call.message.edit_caption(caption=call.message.caption + "\n\n\u2705 \u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u043e")
    await call.answer()

@dp.callback_query(F.data.startswith("reject_order_"))
async def reject_order(call: types.CallbackQuery):
    if call.from_user.id != FOUNDER_ID: return await call.answer()
    order_id = call.data.replace("reject_order_", "")
    order = orders.get(order_id)
    if not order: return await call.answer()
    order["status"] = "rejected"
    try:
        await bot.send_message(order["buyer_id"], f"\u274C \u041a\u043e\u043c\u0438\u0441\u0441\u0438\u044f \u043e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u0430. \u0417\u0430\u043a\u0430\u0437 #{order_id} \u0430\u043d\u043d\u0443\u043b\u0438\u0440\u043e\u0432\u0430\u043d.")
    except: pass
    await call.message.edit_caption(caption=call.message.caption + "\n\n\u274C \u041e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u043e")
    await call.answer()

@dp.message(Command("finditems"))
async def find_items(msg: types.Message):
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2: return await msg.answer("/finditems \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435")
    query = parts[1].lower().strip()
    uid = msg.from_user.id
    found = [l for l in listings if l["user_id"] != uid and query in l.get("item_name", "").lower()]
    if not found:
        await msg.answer(f"\u041f\u043e \u0437\u0430\u043f\u0440\u043e\u0441\u0443 '{parts[1]}' \u043d\u0438\u0447\u0435\u0433\u043e \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e. \u041f\u043e\u043a\u0430\u0437\u044b\u0432\u0430\u044e \u043e\u0431\u044b\u0447\u043d\u0443\u044e \u043b\u0435\u043d\u0442\u0443:")
        return await show_listing(msg, uid, 0)
    for i, l in enumerate(found[:5]):
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="\U0001F6D2 \u041a\u0443\u043f\u0438\u0442\u044c", callback_data=f"buy_{l['id']}")
        ]])
        order_id = l.get("order_id", "??????")
        await msg.answer_photo(l["photo_id"], caption=f"\U0001F4DD {l['description']}\n\n\U0001F4CB \u0417\u0430\u043a\u0430\u0437 #{order_id}", reply_markup=kb)

@dp.message(Command("find"))
async def find_order(msg: types.Message):
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("/find #XXXXXX")
    order_id = parts[1].lstrip("#").upper()
    order = orders.get(order_id)
    if not order: return await msg.answer(f"\u0417\u0430\u043a\u0430\u0437 #{order_id} \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.")
    status_map = {"pending": "\u041e\u0436\u0438\u0434\u0430\u0435\u0442", "confirmed": "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d", "rejected": "\u041e\u0442\u043a\u043b\u043e\u043d\u0451\u043d"}
    await msg.answer(f"\U0001F4CB \u0417\u0430\u043a\u0430\u0437 #{order_id}\n\U0001F4B0 {int(order['amount']):,}\n\U0001F4B3 {int(order['commission']):,}\n\U0001F4CA {status_map.get(order['status'], order['status'])}")

@dp.message(Command("givepublication"))
async def give_publication(msg: types.Message):
    if msg.from_user.id != FOUNDER_ID: return
    parts = msg.text.split()
    if len(parts) < 3: return await msg.answer("/givepublication @nik qty")
    username = parts[1].lstrip("@")
    try: qty = int(parts[2])
    except: return await msg.answer("\u041d\u0435\u0432\u0435\u0440\u043d\u043e\u0435 \u043a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e.")
    target = next((uid for uid, u in users.items() if u.get("username") == username), None)
    if not target: return await msg.answer(f"@{username} \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.")
    users[target]["extra_pubs"] = users[target].get("extra_pubs", 0) + qty
    try: await bot.send_message(target, f"\U0001F4E6 \u0412\u0430\u043c \u0432\u044b\u0434\u0430\u043d\u043e {qty} \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0439!")
    except: pass
    await msg.answer(f"\u2705 @{username} \u0432\u044b\u0434\u0430\u043d\u043e {qty} \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0439.")

@dp.message(Command("delete"))
async def delete_listing_cmd(msg: types.Message):
    if msg.from_user.id != FOUNDER_ID: return
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("/delete #XXXXXX")
    order_id = parts[1].lstrip("#").upper()
    listing = next((l for l in listings if l.get("order_id") == order_id), None)
    if not listing: return await msg.answer(f"\u041e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u0435 #{order_id} \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e.")
    listings.remove(listing)
    await msg.answer(f"\u2705 \u041e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u0435 #{order_id} \u0443\u0434\u0430\u043b\u0435\u043d\u043e.")

@dp.message(F.text == B_PAN)
async def panel(msg: types.Message, state: FSMContext):
    uid = msg.from_user.id
    u = get_user(uid)
    if u["role"] not in ("admin", "founder", "support"):
        await msg.answer("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043b\u044e\u0447 (7 \u0446\u0438\u0444\u0440):")
        await state.set_state(S.auth)
        return
    await show_panel(msg, uid)

async def show_panel(msg, uid):
    role = users[uid]["role"]
    r_count = len([r for r in reports if not r["answered"]])
    s_count = len([s for s in support_msgs if not s["answered"]])
    text = f"\U0001F527 \u041f\u0430\u043d\u0435\u043b\u044c | {ROLES[role]}\n\n"
    if role in ("admin", "founder"):
        text += f"\U0001F6A8 \u0420\u0435\u043f\u043e\u0440\u0442\u043e\u0432: {r_count}\n\U0001F4AC \u041e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0439: {s_count}\n\n"
        text += "/reports\n/supports\n/ban @nik\n/pubban @nik [min]\n/remove_limit @nik\n/demote @nik\n"
    if role == "support":
        text += f"\U0001F4AC \u041e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0439: {s_count}\n\n/supports\n"
        ans = users[uid].get("support_answers", 0)
        text += f"\U0001F4CA \u041e\u0442\u0432\u0435\u0442\u043e\u0432: {ans}/500"
        if ans >= PROMOTE_THRESHOLD:
            text += "\n/promote_request"
    if role == "founder":
        text += "/assign\n/givepublication @nik qty\n/delete #order\n"
    await msg.answer(text)

@dp.message(S.auth, F.text)
async def auth_key(msg: types.Message, state: FSMContext):
    key = msg.text.strip()
    uid = msg.from_user.id
    if key in admin_keys and not admin_keys[key].get("used") and admin_keys[key]["target_id"] == uid:
        info = admin_keys[key]
        users[uid]["role"] = info["role"]
        admin_keys[key]["used"] = True
        await state.clear()
        await msg.answer(f"\u0410\u0432\u0442\u043e\u0440\u0438\u0437\u043e\u0432\u0430\u043d \u043a\u0430\u043a {ROLES[info['role']]}!", reply_markup=main_kb())
        await show_panel(msg, uid)
    else:
        await state.clear()
        await msg.answer("\u041d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 \u043a\u043b\u044e\u0447.")

@dp.message(Command("reports"))
async def list_reports(msg: types.Message):
    if users.get(msg.from_user.id, {}).get("role") not in ("admin", "founder"): return
    unanswered = [r for r in reports if not r["answered"]]
    if not unanswered: return await msg.answer("\u041d\u0435\u0442 \u043d\u043e\u0432\u044b\u0445.")
    text = "\U0001F6A8 \u0420\u0435\u043f\u043e\u0440\u0442\u044b:\n\n"
    for r in unanswered[:10]:
        text += f"#{r['id']} @{r['from_username']}: {r['text'][:50]}\n/reply_report_{r['id']}\n\n"
    await msg.answer(text)

@dp.message(F.text.regexp(r'^/reply_report_\d+$'))
async def reply_report_cmd(msg: types.Message, state: FSMContext):
    if users.get(msg.from_user.id, {}).get("role") not in ("admin", "founder"): return
    rid = int(msg.text.split("_")[-1])
    await state.update_data(reply_id=rid)
    await msg.answer(f"\u041e\u0442\u0432\u0435\u0442 \u043d\u0430 \u0440\u0435\u043f\u043e\u0440\u0442 #{rid}:")
    await state.set_state(S.reply_report)

@dp.message(S.reply_report, F.text)
async def send_reply_report(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    r = next((x for x in reports if x["id"] == data["reply_id"]), None)
    if r:
        r["answered"] = True
        try: await bot.send_message(r["from_id"], f"\u041e\u0442\u0432\u0435\u0442 \u043d\u0430 \u0440\u0435\u043f\u043e\u0440\u0442 #{r['id']}:\n{msg.text}")
        except: pass
    await state.clear()
    await msg.answer("\u041e\u0442\u0432\u0435\u0442 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d.")

@dp.message(Command("supports"))
async def list_supports(msg: types.Message):
    if users.get(msg.from_user.id, {}).get("role") not in ("support", "admin", "founder"): return
    unanswered = [s for s in support_msgs if not s["answered"]]
    if not unanswered: return await msg.answer("\u041d\u0435\u0442 \u043d\u043e\u0432\u044b\u0445.")
    text = "\U0001F4AC \u041e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u044f:\n\n"
    for s in unanswered[:10]:
        text += f"#{s['id']} @{s['from_username']}: {s['text'][:50]}\n/reply_support_{s['id']}\n\n"
    await msg.answer(text)

@dp.message(F.text.regexp(r'^/reply_support_\d+$'))
async def reply_support_cmd(msg: types.Message, state: FSMContext):
    if users.get(msg.from_user.id, {}).get("role") not in ("support", "admin", "founder"): return
    sid = int(msg.text.split("_")[-1])
    await state.update_data(reply_id=sid)
    await msg.answer(f"\u041e\u0442\u0432\u0435\u0442 \u043d\u0430 \u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0435 #{sid}:")
    await state.set_state(S.reply_support)

@dp.message(S.reply_support, F.text)
async def send_reply_support(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = msg.from_user.id
    s = next((x for x in support_msgs if x["id"] == data["reply_id"]), None)
    if s:
        s["answered"] = True
        if users.get(uid, {}).get("role") == "support":
            users[uid]["support_answers"] = users[uid].get("support_answers", 0) + 1
        try: await bot.send_message(s["from_id"], f"\u041e\u0442\u0432\u0435\u0442 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0438 #{s['id']}:\n{msg.text}")
        except: pass
    await state.clear()
    await msg.answer("\u041e\u0442\u0432\u0435\u0442 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d.")

@dp.message(Command("assign"))
async def assign_cmd(msg: types.Message, state: FSMContext):
    if msg.from_user.id != FOUNDER_ID: return
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="\u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430", callback_data="assign_support"),
        InlineKeyboardButton(text="\u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440", callback_data="assign_admin")
    ]])
    await msg.answer("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0440\u043e\u043b\u044c:", reply_markup=kb)

@dp.callback_query(F.data.startswith("assign_"))
async def assign_role_select(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != FOUNDER_ID: return await call.answer()
    role = "support" if call.data == "assign_support" else "admin"
    await state.update_data(assign_role=role)
    await call.message.answer(f"\u0412\u0432\u0435\u0434\u0438\u0442\u0435 @\u043d\u0438\u043a \u0434\u043b\u044f {ROLES[role]}:")
    await state.set_state(S.assign_user)
    await call.answer()

@dp.message(S.assign_user, F.text)
async def assign_user(msg: types.Message, state: FSMContext):
    if msg.from_user.id != FOUNDER_ID:
        await state.clear()
        return
    data = await state.get_data()
    role = data.get("assign_role", "support")
    username = msg.text.strip().lstrip("@")
    target_id = next((uid for uid, u in users.items() if u.get("username") == username), None)
    if not target_id:
        await state.clear()
        return await msg.answer(f"@{username} \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.")
    key = gen_key()
    admin_keys[key] = {"role": role, "target_id": target_id, "used": False}
    try:
        await bot.send_message(target_id, f"\u0412\u044b \u043d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u044b: {ROLES[role]}!\n\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u041f\u0430\u043d\u0435\u043b\u044c \u0438 \u0432\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043b\u044e\u0447.")
    except: pass
    await state.clear()
    await msg.answer(f"@{username} \u043d\u0430\u0437\u043d\u0430\u0447\u0435\u043d {ROLES[role]}.\n\u041a\u043b\u044e\u0447: {key}")

@dp.message(Command("promote_request"))
async def promote_request(msg: types.Message):
    uid = msg.from_user.id
    u = get_user(uid)
    if u["role"] != "support": return await msg.answer("\u0422\u043e\u043b\u044c\u043a\u043e \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430.")
    if u.get("support_answers", 0) < PROMOTE_THRESHOLD:
        return await msg.answer(f"\u041d\u0443\u0436\u043d\u043e \u0435\u0449\u0451 {PROMOTE_THRESHOLD - u.get('support_answers',0)} \u043e\u0442\u0432\u0435\u0442\u043e\u0432.")
    if promote_requests.get(uid): return await msg.answer("\u0417\u0430\u044f\u0432\u043a\u0430 \u0443\u0436\u0435 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0430.")
    promote_requests[uid] = True
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="\u041f\u043e\u0432\u044b\u0441\u0438\u0442\u044c", callback_data=f"promote_{uid}")
    ]])
    try:
        await bot.send_message(FOUNDER_ID, f"\u0417\u0430\u044f\u0432\u043a\u0430 \u043d\u0430 \u043f\u043e\u0432\u044b\u0448\u0435\u043d\u0438\u0435\n@{u['username']}\n\u041e\u0442\u0432\u0435\u0442\u043e\u0432: {u.get('support_answers',0)}", reply_markup=kb)
    except: pass
    await msg.answer("\u0417\u0430\u044f\u0432\u043a\u0430 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0430!")

@dp.callback_query(F.data.startswith("promote_"))
async def promote_user(call: types.CallbackQuery):
    if call.from_user.id != FOUNDER_ID: return await call.answer()
    target_id = int(call.data.split("_")[1])
    if target_id in users:
        users[target_id]["role"] = "admin"
        promote_requests.pop(target_id, None)
        uname = users[target_id]["username"]
        try: await bot.send_message(target_id, "\u0412\u044b \u043f\u043e\u0432\u044b\u0448\u0435\u043d\u044b \u0434\u043e \u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0430!")
        except: pass
        await call.message.edit_text(f"@{uname} \u043f\u043e\u0432\u044b\u0448\u0435\u043d.")
    await call.answer()

@dp.message(Command("demote"))
async def demote_cmd(msg: types.Message, state: FSMContext):
    await state.clear()
    if users.get(msg.from_user.id, {}).get("role") not in ("admin", "founder"): return
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("/demote @nik")
    username = parts[1].lstrip("@")
    target = next((uid for uid, u in users.items() if u.get("username") == username), None)
    if not target: return await msg.answer(f"@{username} \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.")
    if users[target]["role"] == "founder": return await msg.answer("\u041d\u0435\u043b\u044c\u0437\u044f.")
    users[target]["role"] = "player"
    try: await bot.send_message(target, "\u0412\u0430\u0448\u0430 \u0440\u043e\u043b\u044c \u0441\u043d\u044f\u0442\u0430.")
    except: pass
    await msg.answer(f"\u0420\u043e\u043b\u044c @{username} \u0441\u043d\u044f\u0442\u0430.")

@dp.message(Command("ban"))
async def ban_cmd(msg: types.Message, state: FSMContext):
    await state.clear()
    if users.get(msg.from_user.id, {}).get("role") not in ("admin", "founder"): return
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("/ban @nik")
    username = parts[1].lstrip("@")
    target = next((uid for uid, u in users.items() if u.get("username") == username), None)
    if not target: return await msg.answer(f"@{username} \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.")
    users[target]["banned"] = True
    try: await bot.send_message(target, "\u0412\u044b \u0437\u0430\u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u0430\u043d\u044b.")
    except: pass
    await msg.answer(f"@{username} \u0437\u0430\u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u0430\u043d.")

@dp.message(Command("pubban"))
async def pubban_cmd(msg: types.Message, state: FSMContext):
    await state.clear()
    if users.get(msg.from_user.id, {}).get("role") not in ("admin", "founder"): return
    parts = msg.text.split()
    if len(parts) < 3: return await msg.answer("/pubban @nik [min]")
    username = parts[1].lstrip("@")
    try: minutes = int(parts[2])
    except: minutes = 60
    target = next((uid for uid, u in users.items() if u.get("username") == username), None)
    if not target: return await msg.answer(f"@{username} \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.")
    users[target]["pub_banned_until"] = time.time() + minutes * 60
    try: await bot.send_message(target, f"\u0417\u0430\u043f\u0440\u0435\u0442 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0439 \u043d\u0430 {minutes} \u043c\u0438\u043d.")
    except: pass
    await msg.answer(f"@{username} \u0437\u0430\u043f\u0440\u0435\u0442 \u043d\u0430 {minutes} \u043c\u0438\u043d.")

@dp.message(Command("remove_limit"))
async def remove_limit(msg: types.Message, state: FSMContext):
    await state.clear()
    if users.get(msg.from_user.id, {}).get("role") not in ("admin", "founder"): return
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("/remove_limit @nik")
    username = parts[1].lstrip("@")
    target = next((uid for uid, u in users.items() if u.get("username") == username), None)
    if not target: return await msg.answer(f"@{username} \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.")
    users[target]["free_pubs"] = FREE_PUBS
    await msg.answer(f"\u041b\u0438\u043c\u0438\u0442 \u0441\u043d\u044f\u0442 \u0434\u043b\u044f @{username}.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
