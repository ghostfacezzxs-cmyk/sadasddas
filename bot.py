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

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

users = {}
listings = []
reports = []
support_msgs = []
admin_keys = {}
promote_requests = {}

ROLES = {"player": "\u0418\u0433\u0440\u043e\u043a", "support": "\u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430", "admin": "\u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440", "founder": "\u041e\u0441\u043d\u043e\u0432\u0430\u0442\u0435\u043b\u044c"}
MAX_LISTINGS = 2
LISTING_COOLDOWN = 1800

B_SELL = "\U0001F4E6 \u041f\u0440\u043e\u0434\u0430\u0442\u044c \u0432\u0435\u0449\u044c"
B_VIEW = "\U0001F6D2 \u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440 \u043f\u0440\u043e\u0434\u0430\u0436"
B_REP  = "\U0001F6A8 \u0420\u0435\u043f\u043e\u0440\u0442"
B_SUP  = "\U0001F4AC \u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430"
B_PRO  = "\U0001F464 \u041f\u0440\u043e\u0444\u0438\u043b\u044c"
B_PAN  = "\U0001F527 \u041f\u0430\u043d\u0435\u043b\u044c"

def get_user(uid, username=""):
    if uid not in users:
        users[uid] = {"role": "player", "username": username, "listings_count": 0,
                      "listings_reset_time": 0, "banned": False, "pub_banned_until": 0,
                      "support_answers": 0}
    if username:
        users[uid]["username"] = username
    return users[uid]

def gen_key():
    return "".join(random.choices(string.digits, k=7))

def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=B_SELL), KeyboardButton(text=B_VIEW)],
        [KeyboardButton(text=B_REP),  KeyboardButton(text=B_SUP)],
        [KeyboardButton(text=B_PRO),  KeyboardButton(text=B_PAN)],
    ], resize_keyboard=True)

class S(StatesGroup):
    photo = State()
    description = State()
    report = State()
    support = State()
    auth = State()
    assign_role = State()
    assign_user = State()
    reply_report = State()
    reply_support = State()

@dp.message(Command("start"))
async def cmd_start(msg: types.Message, state: FSMContext):
    await state.clear()
    uid = msg.from_user.id
    uname = msg.from_user.username or str(uid)
    u = get_user(uid, uname)
    if uid == FOUNDER_ID:
        u["role"] = "founder"
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
    ans = u.get("support_answers", 0)
    promo = f"\n\u041e\u0442\u0432\u0435\u0442\u043e\u0432: {ans}/500" if u["role"] == "support" else ""
    await msg.answer(f"\u041f\u0440\u043e\u0444\u0438\u043b\u044c\n\n\u041d\u0438\u043a: @{u['username']}\n\u0421\u0442\u0430\u0442\u0443\u0441: {ROLES[u['role']]}\n\u041e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u0439: {u['listings_count']}/{MAX_LISTINGS}\n\u0410\u043a\u043a\u0430\u0443\u043d\u0442: {ban_s}\n\u041f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438: {pub_s}{promo}")

@dp.message(F.text == B_SELL)
async def sell_start(msg: types.Message, state: FSMContext):
    await state.clear()
    uid = msg.from_user.id
    u = get_user(uid)
    if u.get("banned"): return await msg.answer("\u0412\u044b \u0437\u0430\u0431\u043b\u043e\u043a\u0438\u0440\u043e\u0432\u0430\u043d\u044b.")
    now = time.time()
    if u.get("pub_banned_until", 0) > now:
        return await msg.answer(f"\u0417\u0430\u043f\u0440\u0435\u0442 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0439. \u041e\u0441\u0442\u0430\u043b\u043e\u0441\u044c {int((u['pub_banned_until']-now)/60)} \u043c\u0438\u043d.")
    if now - u["listings_reset_time"] >= LISTING_COOLDOWN:
        u["listings_count"] = 0
        u["listings_reset_time"] = now
    if u["listings_count"] >= MAX_LISTINGS:
        left = int((u["listings_reset_time"] + LISTING_COOLDOWN - now) / 60)
        return await msg.answer(f"\u041b\u0438\u043c\u0438\u0442 {MAX_LISTINGS} \u043e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u044f. \u041f\u043e\u0434\u043e\u0436\u0434\u0438\u0442\u0435 {left} \u043c\u0438\u043d.")
    await msg.answer("\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0444\u043e\u0442\u043e \u0432\u0430\u0448\u0435\u0439 \u0432\u0435\u0449\u0438:")
    await state.set_state(S.photo)

@dp.message(S.photo, F.photo)
async def sell_photo(msg: types.Message, state: FSMContext):
    await state.update_data(photo_id=msg.photo[-1].file_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="\u0414\u0430", callback_data="desc_yes"),
        InlineKeyboardButton(text="\u041d\u0435\u0442", callback_data="desc_no")
    ]])
    await msg.answer("\u041e\u0442\u043b\u0438\u0447\u043d\u043e! \u041d\u0443\u0436\u043d\u043e \u043b\u0438 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435?", reply_markup=kb)

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
    listings.append({"id": len(listings)+1, "user_id": uid, "username": uname,
                     "photo_id": data.get("photo_id"),
                     "description": data.get("description", "\u0411\u0435\u0437 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u044f"),
                     "time": time.time()})
    u["listings_count"] += 1
    await state.clear()
    await msg.answer("\u041e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u0435 \u043e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d\u043e!", reply_markup=main_kb())

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
        InlineKeyboardButton(text="\u041d\u0430\u043f\u0438\u0441\u0430\u0442\u044c", callback_data=f"contact_{l['user_id']}")
    ]])
    await msg.answer_photo(l["photo_id"], caption=f"@{l['username']}\n{l['description']}", reply_markup=kb)

@dp.callback_query(F.data.startswith("next_"))
async def next_listing(call: types.CallbackQuery):
    _, idx, uid = call.data.split("_")
    await show_listing(call.message, int(uid), int(idx))
    await call.answer()

@dp.callback_query(F.data.startswith("contact_"))
async def contact_seller(call: types.CallbackQuery):
    sid = int(call.data.split("_")[1])
    uname = users.get(sid, {}).get("username", str(sid))
    await call.message.answer(f"\u041d\u0430\u043f\u0438\u0448\u0438\u0442\u0435 \u043f\u0440\u043e\u0434\u0430\u0432\u0446\u0443: @{uname}")
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
    rid = len(reports) + 1
    reports.append({"id": rid, "from_id": uid, "from_username": uname, "text": msg.text, "answered": False})
    await state.clear()
    await msg.answer("\u0420\u0435\u043f\u043e\u0440\u0442 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d!", reply_markup=main_kb())
    for aid, u in users.items():
        if u["role"] in ("admin", "founder"):
            try: await bot.send_message(aid, f"\u0420\u0435\u043f\u043e\u0440\u0442 #{rid}\n@{uname}\n{msg.text}\n\n/reply_report_{rid}")
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
    sid = len(support_msgs) + 1
    support_msgs.append({"id": sid, "from_id": uid, "from_username": uname, "text": msg.text, "answered": False})
    await state.clear()
    await msg.answer("\u041e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e \u0432 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0443!", reply_markup=main_kb())
    for aid, u in users.items():
        if u["role"] in ("support", "admin", "founder"):
            try: await bot.send_message(aid, f"\u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430 #{sid}\n@{uname}\n{msg.text}\n\n/reply_support_{sid}")
            except: pass

@dp.message(F.text == B_PAN)
async def panel(msg: types.Message, state: FSMContext):
    uid = msg.from_user.id
    u = get_user(uid)
    if u["role"] not in ("admin", "founder", "support"):
        await msg.answer("\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043b\u044e\u0447 \u0434\u043e\u0441\u0442\u0443\u043f\u0430 (7 \u0446\u0438\u0444\u0440):")
        await state.set_state(S.auth)
        return
    await show_panel(msg, uid)

async def show_panel(msg, uid):
    role = users[uid]["role"]
    r_count = len([r for r in reports if not r["answered"]])
    s_count = len([s for s in support_msgs if not s["answered"]])
    text = f"\U0001F527 \u041f\u0430\u043d\u0435\u043b\u044c | {ROLES[role]}\n\n"
    if role in ("admin", "founder"):
        text += f"\U0001F6A8 \u0420\u0435\u043f\u043e\u0440\u0442\u043e\u0432: {r_count}\n"
        text += f"\U0001F4AC \u041e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0439: {s_count}\n\n"
        text += "\U0001F4CB \u041a\u043e\u043c\u0430\u043d\u0434\u044b:\n"
        text += "/reports \u2014 \u0440\u0435\u043f\u043e\u0440\u0442\u044b\n"
        text += "/supports \u2014 \u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u044f\n"
        text += "/ban @\u043d\u0438\u043a \u2014 \u0431\u0430\u043d\n"
        text += "/pubban @\u043d\u0438\u043a [\u043c\u0438\u043d] \u2014 \u0437\u0430\u043f\u0440\u0435\u0442 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0439\n"
        text += "/remove_limit @\u043d\u0438\u043a \u2014 \u0441\u043d\u044f\u0442\u044c \u043b\u0438\u043c\u0438\u0442\n"
        text += "/demote @\u043d\u0438\u043a \u2014 \u0441\u043d\u044f\u0442\u044c \u0440\u043e\u043b\u044c\n"
    if role == "support":
        text += f"\U0001F4AC \u041e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0439: {s_count}\n\n"
        text += "/supports \u2014 \u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u044f\n"
        ans = users[uid].get("support_answers", 0)
        text += f"\n\U0001F4CA \u0412\u0430\u0448\u0438\u0445 \u043e\u0442\u0432\u0435\u0442\u043e\u0432: {ans}/500"
        if ans >= PROMOTE_THRESHOLD:
            text += "\n\u2705 /promote_request \u2014 \u043f\u043e\u0434\u0430\u0442\u044c \u043d\u0430 \u043f\u043e\u0432\u044b\u0448\u0435\u043d\u0438\u0435"
    if role == "founder":
        text += "/assign \u2014 \u043d\u0430\u0437\u043d\u0430\u0447\u0438\u0442\u044c \u0440\u043e\u043b\u044c\n"
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
    if not unanswered: return await msg.answer("\u041d\u0435\u0442 \u043d\u043e\u0432\u044b\u0445 \u0440\u0435\u043f\u043e\u0440\u0442\u043e\u0432.")
    text = "\u0420\u0435\u043f\u043e\u0440\u0442\u044b:\n\n"
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
    if not unanswered: return await msg.answer("\u041d\u0435\u0442 \u043d\u043e\u0432\u044b\u0445 \u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u0439.")
    text = "\u041e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u044f:\n\n"
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
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430", callback_data="assign_support"),
         InlineKeyboardButton(text="\u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440", callback_data="assign_admin")]
    ])
    await msg.answer("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0440\u043e\u043b\u044c:", reply_markup=kb)

@dp.callback_query(F.data.startswith("assign_"))
async def assign_role_select(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != FOUNDER_ID: return await call.answer()
    role = "support" if call.data == "assign_support" else "admin"
    await state.update_data(assign_role=role)
    await call.message.answer(f"\u0412\u0432\u0435\u0434\u0438\u0442\u0435 @\u043d\u0438\u043a \u0438\u0433\u0440\u043e\u043a\u0430 \u0434\u043b\u044f \u043d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u044f \u043d\u0430 {ROLES[role]}:")
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
        return await msg.answer(f"@{username} \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d. \u041e\u043d \u0434\u043e\u043b\u0436\u0435\u043d \u043d\u0430\u043f\u0438\u0441\u0430\u0442\u044c /start.")
    key = gen_key()
    admin_keys[key] = {"role": role, "target_id": target_id, "used": False}
    try:
        await bot.send_message(target_id, f"\u0412\u044b \u043d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u044b: {ROLES[role]}!\n\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u041f\u0430\u043d\u0435\u043b\u044c \u0438 \u0432\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043b\u044e\u0447 \u0434\u043b\u044f \u0432\u0445\u043e\u0434\u0430.")
    except: pass
    await state.clear()
    await msg.answer(f"@{username} \u043d\u0430\u0437\u043d\u0430\u0447\u0435\u043d {ROLES[role]}.\n\u041a\u043b\u044e\u0447 (\u043f\u0435\u0440\u0435\u0434\u0430\u0439\u0442\u0435 \u043b\u0438\u0447\u043d\u043e): {key}")

@dp.message(Command("promote_request"))
async def promote_request(msg: types.Message):
    uid = msg.from_user.id
    u = get_user(uid)
    if u["role"] != "support": return await msg.answer("\u0422\u043e\u043b\u044c\u043a\u043e \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430 \u043c\u043e\u0436\u0435\u0442 \u043f\u043e\u0434\u0430\u0442\u044c.")
    if u.get("support_answers", 0) < PROMOTE_THRESHOLD:
        return await msg.answer(f"\u041d\u0443\u0436\u043d\u043e \u0435\u0449\u0451 {PROMOTE_THRESHOLD - u.get('support_answers',0)} \u043e\u0442\u0432\u0435\u0442\u043e\u0432.")
    if promote_requests.get(uid): return await msg.answer("\u0417\u0430\u044f\u0432\u043a\u0430 \u0443\u0436\u0435 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0430.")
    promote_requests[uid] = True
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="\u041f\u043e\u0432\u044b\u0441\u0438\u0442\u044c \u0434\u043e \u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0430", callback_data=f"promote_{uid}")
    ]])
    try:
        await bot.send_message(FOUNDER_ID,
            f"\u0417\u0430\u044f\u0432\u043a\u0430 \u043d\u0430 \u043f\u043e\u0432\u044b\u0448\u0435\u043d\u0438\u0435\n@{u['username']}\n\u041e\u0442\u0432\u0435\u0442\u043e\u0432: {u.get('support_answers',0)}",
            reply_markup=kb)
    except: pass
    await msg.answer("\u0417\u0430\u044f\u0432\u043a\u0430 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0430!")

@dp.callback_query(F.data.startswith("promote_"))
async def promote_user(call: types.CallbackQuery):
    if call.from_user.id != FOUNDER_ID: return await call.answer("\u041d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u0430.")
    target_id = int(call.data.split("_")[1])
    if target_id in users:
        users[target_id]["role"] = "admin"
        promote_requests.pop(target_id, None)
        uname = users[target_id]["username"]
        try: await bot.send_message(target_id, "\u0412\u044b \u043f\u043e\u0432\u044b\u0448\u0435\u043d\u044b \u0434\u043e \u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0430!")
        except: pass
        await call.message.edit_text(f"@{uname} \u043f\u043e\u0432\u044b\u0448\u0435\u043d \u0434\u043e \u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0430.")
    await call.answer()

@dp.message(Command("demote"))
async def demote_cmd(msg: types.Message, state: FSMContext):
    await state.clear()
    if users.get(msg.from_user.id, {}).get("role") not in ("admin", "founder"): return
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("\u0424\u043e\u0440\u043c\u0430\u0442: /demote @\u043d\u0438\u043a")
    username = parts[1].lstrip("@")
    target = next((uid for uid, u in users.items() if u.get("username") == username), None)
    if not target: return await msg.answer(f"@{username} \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.")
    if users[target]["role"] == "founder": return await msg.answer("\u041d\u0435\u043b\u044c\u0437\u044f \u0441\u043d\u044f\u0442\u044c \u043e\u0441\u043d\u043e\u0432\u0430\u0442\u0435\u043b\u044f.")
    users[target]["role"] = "player"
    try: await bot.send_message(target, "\u0412\u0430\u0448\u0430 \u0440\u043e\u043b\u044c \u0431\u044b\u043b\u0430 \u0441\u043d\u044f\u0442\u0430. \u041f\u0430\u043d\u0435\u043b\u044c \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u0430.")
    except: pass
    await msg.answer(f"\u0420\u043e\u043b\u044c @{username} \u0441\u043d\u044f\u0442\u0430.")

@dp.message(Command("ban"))
async def ban_cmd(msg: types.Message, state: FSMContext):
    await state.clear()
    if users.get(msg.from_user.id, {}).get("role") not in ("admin", "founder"): return
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("\u0424\u043e\u0440\u043c\u0430\u0442: /ban @\u043d\u0438\u043a")
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
    if len(parts) < 3: return await msg.answer("\u0424\u043e\u0440\u043c\u0430\u0442: /pubban @\u043d\u0438\u043a [\u043c\u0438\u043d\u0443\u0442\u044b]")
    username = parts[1].lstrip("@")
    try: minutes = int(parts[2])
    except: minutes = 60
    target = next((uid for uid, u in users.items() if u.get("username") == username), None)
    if not target: return await msg.answer(f"@{username} \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.")
    users[target]["pub_banned_until"] = time.time() + minutes * 60
    try: await bot.send_message(target, f"\u0417\u0430\u043f\u0440\u0435\u0442 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0439 \u043d\u0430 {minutes} \u043c\u0438\u043d.")
    except: pass
    await msg.answer(f"@{username} \u0437\u0430\u043f\u0440\u0435\u0442 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0439 \u043d\u0430 {minutes} \u043c\u0438\u043d.")

@dp.message(Command("remove_limit"))
async def remove_limit(msg: types.Message, state: FSMContext):
    await state.clear()
    if users.get(msg.from_user.id, {}).get("role") not in ("admin", "founder"): return
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("\u0424\u043e\u0440\u043c\u0430\u0442: /remove_limit @\u043d\u0438\u043a")
    username = parts[1].lstrip("@")
    target = next((uid for uid, u in users.items() if u.get("username") == username), None)
    if not target: return await msg.answer(f"@{username} \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.")
    users[target]["listings_count"] = 0
    users[target]["listings_reset_time"] = 0
    await msg.answer(f"\u041b\u0438\u043c\u0438\u0442 \u0441\u043d\u044f\u0442 \u0434\u043b\u044f @{username}.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
