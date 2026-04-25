"""
🤖 Agent Nazorat Boti - To'liq versiya 3.0
==========================================
Rollar: Admin, Supervayzor, Menejer, Agent
"""

import telebot
from telebot import types
from datetime import datetime, date, timedelta
import json, os, time

# =============================================
BOT_TOKEN = "8663649354:AAGDw8eBwEVb5ck7yEbb4hX6Ya3cCZAUxMY"
ADMIN_ID  = 7642574758
# =============================================

PRODUCTS = [
    {"name": "🥪 Sendwich",         "price": 10000},
    {"name": "🧒 Detskiy sendwich", "price": 5000},
    {"name": "🍗 Tovuqli sendwich", "price": 12000},
    {"name": "🍔 Burger",           "price": 15000},
]

ROLES = {
    "admin":       "👑 Admin",
    "supervisor":  "🔷 Supervayzor",
    "manager":     "🔶 Menejer",
    "agent":       "👤 Agent",
}

bot       = telebot.TeleBot(BOT_TOKEN)
DATA_FILE = "bot_data.json"
sessions  = {}

# ──────────────────────────────────────────
# 🗄 Ma'lumotlar
# ──────────────────────────────────────────
def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "reports": [], "pending": {}}

def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(uid):
    return load()["users"].get(str(uid))

def is_admin(uid):
    return uid == ADMIN_ID

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def fmt(n):
    return f"{n:,}".replace(",", " ")

# ──────────────────────────────────────────
# Klaviaturalar
# ──────────────────────────────────────────
def main_kb(role):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if role == "agent":
        kb.add("🛒 Savdoni boshlash")
        kb.add("📊 Mening hisobotlarim")
    elif role in ("supervisor", "manager"):
        kb.add("📊 Hisobotlar", "👥 Agentlar")
        kb.add("💰 Sotuv statistikasi", "🏆 Reyting")
    return kb

def admin_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📊 Hisobotlar", "👥 Foydalanuvchilar")
    kb.add("💰 Sotuv statistikasi", "🏆 Reyting")
    kb.add("⏳ Kutayotganlar")
    return kb

def cancel_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("❌ Bekor qilish")
    return kb

def location_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📍 Lokatsiyani yuborish", request_location=True))
    kb.add("❌ Bekor qilish")
    return kb

def products_kb(counts):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i, p in enumerate(PRODUCTS):
        cnt = counts.get(str(i), 0)
        label = f"{p['name']} [{cnt} ta]" if cnt > 0 else p['name']
        kb.add(label)
    kb.add("✅ Tayyor", "❌ Bekor qilish")
    return kb

def qty_confirm_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✅ Tasdiqlash")
    kb.add("❌ Bekor qilish")
    return kb

def reports_filter_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📅 Bugun", "📆 Bu oy")
    kb.add("🗓 Sana oralig'i tanlash")
    kb.add("📤 Excel yuklab olish", "❌ Yopish")
    return kb

# ──────────────────────────────────────────
# /start
# ──────────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    uid = msg.from_user.id

    if is_admin(uid):
        data = load()
        if str(uid) not in data["users"]:
            data["users"][str(uid)] = {
                "name": "Admin",
                "role": "admin",
                "registered": now_str(),
                "approved": True,
            }
            save(data)
        bot.send_message(uid, "👑 <b>Admin panel</b>\nXush kelibsiz!",
            parse_mode="HTML", reply_markup=admin_kb())
        return

    user = get_user(uid)
    if user:
        if not user.get("approved"):
            bot.send_message(uid, "⏳ Sizning so'rovingiz hali tasdiqlanmagan. Kuting.")
            return
        bot.send_message(uid,
            f"👋 Xush kelibsiz, <b>{user['name']}</b>! ({ROLES.get(user['role'],'')}) ",
            parse_mode="HTML", reply_markup=main_kb(user["role"]))
    else:
        bot.send_message(uid,
            "👋 Salom! Botdan foydalanish uchun\n"
            "<b>Ism Familiyangizni</b> yuboring:",
            parse_mode="HTML")
        sessions[uid] = {"step": "register_name"}

# ──────────────────────────────────────────
# Ro'yxatdan o'tish va tasdiqlash
# ──────────────────────────────────────────
@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "register_name")
def register_name(msg):
    uid  = msg.from_user.id
    name = msg.text.strip()
    sessions[uid] = {"step": "register_role", "name": name}

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👤 Agent", "🔷 Supervayzor", "🔶 Menejer")
    bot.send_message(uid, f"Ismingiz: <b>{name}</b>\n\nRolingizni tanlang:",
        parse_mode="HTML", reply_markup=kb)

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "register_role")
def register_role(msg):
    uid  = msg.from_user.id
    text = msg.text.strip()
    role_map = {
        "👤 Agent": "agent",
        "🔷 Supervayzor": "supervisor",
        "🔶 Menejer": "manager",
    }
    if text not in role_map:
        bot.send_message(uid, "⚠️ Tugmalardan birini bosing.")
        return

    role = role_map[text]
    name = sessions[uid]["name"]
    sessions.pop(uid, None)

    data = load()
    data["pending"][str(uid)] = {
        "uid": uid,
        "name": name,
        "role": role,
        "username": msg.from_user.username or "",
        "time": now_str(),
    }
    save(data)

    bot.send_message(uid,
        "✅ So'rovingiz yuborildi!\n\n"
        "⏳ Admin tasdiqlashini kuting.\n"
        "Tasdiqlangach xabar olasiz.",
        reply_markup=types.ReplyKeyboardRemove())

    # Adminga xabar
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{uid}_{role}"),
        types.InlineKeyboardButton("❌ Rad etish",  callback_data=f"reject_{uid}"),
    )
    bot.send_message(ADMIN_ID,
        f"🆕 <b>Yangi so'rov</b>\n\n"
        f"👤 Ism: {name}\n"
        f"🆔 ID: {uid}\n"
        f"📱 @{msg.from_user.username or 'username yo\'q'}\n"
        f"🎭 Rol: {ROLES[role]}\n"
        f"📅 {now_str()}",
        parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("approve_"))
def approve_user(call):
    parts = call.data.split("_")
    uid   = int(parts[1])
    role  = parts[2]

    data = load()
    pending = data["pending"].get(str(uid))
    if not pending:
        bot.answer_callback_query(call.id, "Topilmadi!")
        return

    data["users"][str(uid)] = {
        "name"      : pending["name"],
        "role"      : role,
        "username"  : pending.get("username", ""),
        "registered": pending["time"],
        "approved"  : True,
        "total_visits": 0,
    }
    data["pending"].pop(str(uid), None)
    save(data)

    bot.answer_callback_query(call.id, "✅ Tasdiqlandi!")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.send_message(call.message.chat.id,
        f"✅ <b>{pending['name']}</b> ({ROLES[role]}) tasdiqlandi!",
        parse_mode="HTML")

    # Foydalanuvchiga xabar
    try:
        user_data = load()["users"][str(uid)]
        bot.send_message(uid,
            f"🎉 Tabriklaymiz, <b>{pending['name']}</b>!\n\n"
            f"Rolingiz: {ROLES[role]}\n"
            "Botdan foydalanishingiz mumkin!",
            parse_mode="HTML", reply_markup=main_kb(role))
    except:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("reject_"))
def reject_user(call):
    uid = int(call.data.split("_")[1])
    data = load()
    pending = data["pending"].get(str(uid))
    if not pending:
        bot.answer_callback_query(call.id, "Topilmadi!")
        return
    data["pending"].pop(str(uid), None)
    save(data)
    bot.answer_callback_query(call.id, "❌ Rad etildi!")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.send_message(call.message.chat.id,
        f"❌ <b>{pending['name']}</b> rad etildi.", parse_mode="HTML")
    try:
        bot.send_message(uid,
            "❌ Afsuski, so'rovingiz rad etildi.\n"
            "Qo'shimcha ma'lumot uchun adminiga murojaat qiling.")
    except:
        pass

# ──────────────────────────────────────────
# Bekor qilish
# ──────────────────────────────────────────
@bot.message_handler(func=lambda m: m.text == "❌ Bekor qilish")
def cancel(msg):
    uid = msg.from_user.id
    sessions.pop(uid, None)
    user = get_user(uid)
    if user and user.get("approved"):
        bot.send_message(uid, "🚫 Bekor qilindi.", reply_markup=main_kb(user["role"]))
    else:
        bot.send_message(uid, "🚫 Bekor qilindi.")

# ──────────────────────────────────────────
# SAVDONI BOSHLASH
# ──────────────────────────────────────────
@bot.message_handler(func=lambda m: m.text == "🛒 Savdoni boshlash")
def start_visit(msg):
    uid  = msg.from_user.id
    user = get_user(uid)
    if not user or not user.get("approved") or user["role"] != "agent":
        return bot.send_message(uid, "❌ Ruxsat yo'q.")

    sessions[uid] = {"step": "shop_name", "report": {
        "agent_id"  : uid,
        "agent_name": user["name"],
        "started"   : now_str(),
        "date"      : today_str(),
    }}
    bot.send_message(uid,
        "🏪 <b>1-qadam: Magazin nomi</b>\n\nMagazin nomini yozing:",
        parse_mode="HTML", reply_markup=cancel_kb())

# QADAM 1 — Magazin nomi
@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "shop_name")
def receive_shop_name(msg):
    uid  = msg.from_user.id
    sess = sessions[uid]
    sess["report"]["shop_name"] = msg.text.strip()
    sess["step"] = "location"
    bot.send_message(uid,
        "📍 <b>2-qadam: Lokatsiya</b>\n\nHozirgi joylashuvingizni yuboring:",
        parse_mode="HTML", reply_markup=location_kb())

# QADAM 2 — Lokatsiya
@bot.message_handler(content_types=["location"])
def receive_location(msg):
    uid  = msg.from_user.id
    sess = sessions.get(uid)
    if not sess or sess["step"] != "location":
        return
    lat = msg.location.latitude
    lon = msg.location.longitude
    sess["report"]["location"] = {"lat": lat, "lon": lon}
    sess["step"] = "photo"
    bot.send_message(uid,
        f"✅ Lokatsiya qabul qilindi!\n\n"
        "📸 <b>3-qadam: Foto</b>\n\n"
        "📷 Kamerani oching va magazin fotoini oling\n"
        "<i>(Faqat kameradan olingan jonli foto qabul qilinadi)</i>",
        parse_mode="HTML", reply_markup=cancel_kb())

# QADAM 3 — Foto (faqat kameradan)
@bot.message_handler(content_types=["photo"])
def receive_photo(msg):
    uid  = msg.from_user.id
    sess = sessions.get(uid)
    if not sess or sess["step"] != "photo":
        return

    # Kameradan olingan foto tekshiruvi
    photo = msg.photo[-1]
    # Agar forward qilingan bo'lsa yoki media_group bo'lsa rad etish
    if msg.forward_date or msg.media_group_id:
        bot.send_message(uid,
            "❌ Faqat kameradan jonli olingan foto yuboring!\n"
            "Galereyadagi yoki boshqa chatdan yuborilgan foto qabul qilinmaydi.")
        return

    # Vaqt tekshiruvi — 2 daqiqadan eski bo'lsa rad etish
    photo_time = msg.date
    current_time = int(time.time())
    if current_time - photo_time > 120:
        bot.send_message(uid,
            "❌ Bu foto eski ko'rinadi!\n"
            "Iltimos, hozir kameradan yangi foto oling.")
        return

    sess["report"]["photo_id"] = photo.file_id
    sess["report"]["photo_time"] = now_str()
    sess["step"] = "products"
    sess["report"]["product_counts"] = {}

    prod_list = "\n".join(
        f"  {i+1}. {p['name']} — {fmt(p['price'])} so'm"
        for i, p in enumerate(PRODUCTS)
    )
    bot.send_message(uid,
        "✅ Foto qabul qilindi!\n\n"
        f"📦 <b>4-qadam: Sotuv mahsulotlari</b>\n\n{prod_list}\n\n"
        "Har bir mahsulotni bosib sonini kiriting:",
        parse_mode="HTML", reply_markup=products_kb({}))

# QADAM 4 — Mahsulot tanlash
@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "products")
def select_product(msg):
    uid  = msg.from_user.id
    sess = sessions[uid]
    text = msg.text

    if text == "✅ Tayyor":
        counts = sess["report"]["product_counts"]
        if not counts:
            bot.send_message(uid, "⚠️ Kamida 1 ta mahsulot kiriting!",
                reply_markup=products_kb({}))
            return
        # Vozvrat bosqichiga o'tish
        sess["step"] = "vozvrat"
        sess["report"]["vozvrat_counts"] = {}
        bot.send_message(uid,
            "🔄 <b>5-qadam: Vozvratlar</b>\n\n"
            "Qaytarilgan mahsulotlarni kiriting.\n"
            "Vozvrat yo'q bo'lsa ✅ Tayyor bosing:",
            parse_mode="HTML", reply_markup=products_kb({}))
        return

    for i, p in enumerate(PRODUCTS):
        cnt = sess["report"]["product_counts"].get(str(i), 0)
        if text == p['name'] or text == f"{p['name']} [{cnt} ta]":
            sess["step"] = "qty_sale"
            sess["selected_product"] = i
            bot.send_message(uid,
                f"📦 <b>{p['name']}</b>\n"
                f"Narxi: {fmt(p['price'])} so'm/dona\n\n"
                "Nechta sotdingiz? Sonini <b>yozing</b> va ✅ Tasdiqlash bosing:",
                parse_mode="HTML", reply_markup=qty_confirm_kb())
            return

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "qty_sale")
def receive_qty_sale(msg):
    uid  = msg.from_user.id
    sess = sessions[uid]
    text = msg.text.strip()
    idx  = sess["selected_product"]
    p    = PRODUCTS[idx]

    if text == "✅ Tasdiqlash":
        try:
            qty = int(sess.get("qty_input", 0))
            if qty < 0: raise ValueError
        except:
            bot.send_message(uid, "⚠️ Avval sonini yozing!", reply_markup=qty_confirm_kb())
            return
        sess.pop("qty_input", None)
        if qty > 0:
            sess["report"]["product_counts"][str(idx)] = qty
        else:
            sess["report"]["product_counts"].pop(str(idx), None)
        sess["step"] = "products"
        summa = qty * p["price"]
        bot.send_message(uid,
            f"✅ <b>{p['name']}</b> — {qty} ta ({fmt(summa)} so'm)",
            parse_mode="HTML",
            reply_markup=products_kb(sess["report"]["product_counts"]))
        return

    # Son kiritildi — saqlab qo'yamiz
    try:
        qty = int(text)
        if qty < 0: raise ValueError
        sess["qty_input"] = qty
        bot.send_message(uid,
            f"📦 <b>{p['name']}</b>\n"
            f"Soni: <b>{qty}</b> ta\n"
            f"Jami: <b>{fmt(qty * p['price'])} so'm</b>\n\n"
            "✅ Tasdiqlash tugmasini bosing:",
            parse_mode="HTML", reply_markup=qty_confirm_kb())
    except ValueError:
        bot.send_message(uid, "⚠️ Faqat son kiriting!", reply_markup=qty_confirm_kb())

# QADAM 5 — Vozvrat
@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "vozvrat")
def select_vozvrat(msg):
    uid  = msg.from_user.id
    sess = sessions[uid]
    text = msg.text

    if text == "✅ Tayyor":
        sess["step"] = "expired"
        bot.send_message(uid,
            "🗑 <b>6-qadam: Eskirgan mahsulotlar</b>\n\n"
            "Muddati o'tgan mahsulotlarni kiriting.\n"
            "<i>Namuna: Sendwich 12.2025 - 3 ta</i>\n\n"
            "Eskirgan yo'q bo'lsa — <b>Yo'q</b> yozing:",
            parse_mode="HTML", reply_markup=cancel_kb())
        return

    for i, p in enumerate(PRODUCTS):
        cnt = sess["report"]["vozvrat_counts"].get(str(i), 0)
        if text == p['name'] or text == f"{p['name']} [{cnt} ta]":
            sess["step"] = "qty_vozvrat"
            sess["selected_product"] = i
            bot.send_message(uid,
                f"🔄 <b>{p['name']}</b>\n\n"
                "Nechta qaytarildi? Sonini <b>yozing</b> va ✅ Tasdiqlash bosing:",
                parse_mode="HTML", reply_markup=qty_confirm_kb())
            return

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "qty_vozvrat")
def receive_qty_vozvrat(msg):
    uid  = msg.from_user.id
    sess = sessions[uid]
    text = msg.text.strip()
    idx  = sess["selected_product"]
    p    = PRODUCTS[idx]

    if text == "✅ Tasdiqlash":
        try:
            qty = int(sess.get("qty_input", 0))
            if qty < 0: raise ValueError
        except:
            bot.send_message(uid, "⚠️ Avval sonini yozing!", reply_markup=qty_confirm_kb())
            return
        sess.pop("qty_input", None)
        if qty > 0:
            sess["report"]["vozvrat_counts"][str(idx)] = qty
        else:
            sess["report"]["vozvrat_counts"].pop(str(idx), None)
        sess["step"] = "vozvrat"
        bot.send_message(uid,
            f"✅ <b>{p['name']}</b> vozvrat — {qty} ta",
            parse_mode="HTML",
            reply_markup=products_kb(sess["report"]["vozvrat_counts"]))
        return

    try:
        qty = int(text)
        if qty < 0: raise ValueError
        sess["qty_input"] = qty
        bot.send_message(uid,
            f"🔄 <b>{p['name']}</b>\n"
            f"Soni: <b>{qty}</b> ta\n\n"
            "✅ Tasdiqlash tugmasini bosing:",
            parse_mode="HTML", reply_markup=qty_confirm_kb())
    except ValueError:
        bot.send_message(uid, "⚠️ Faqat son kiriting!", reply_markup=qty_confirm_kb())

# QADAM 6 — Eskirgan
@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "expired")
def receive_expired(msg):
    uid  = msg.from_user.id
    sess = sessions[uid]
    text = msg.text.strip()

    if text.lower() in ["yo'q", "yoq", "нет", "no", "-"]:
        sess["report"]["expired"] = []
    else:
        sess["report"]["expired"] = [l.strip() for l in text.splitlines() if l.strip()]

    sess["report"]["finished"] = now_str()
    r = sess["report"]

    # Sotuv hisobi
    sale_lines, total_sale = [], 0
    for idx, qty in r.get("product_counts", {}).items():
        p = PRODUCTS[int(idx)]
        s = qty * p["price"]
        total_sale += s
        sale_lines.append(f"  • {p['name']}: {qty} ta = {fmt(s)} so'm")

    # Vozvrat hisobi
    vozv_lines, total_vozv = [], 0
    for idx, qty in r.get("vozvrat_counts", {}).items():
        p = PRODUCTS[int(idx)]
        s = qty * p["price"]
        total_vozv += s
        vozv_lines.append(f"  • {p['name']}: {qty} ta = {fmt(s)} so'm")

    net_total = total_sale - total_vozv
    exp_txt   = "\n".join(f"  ⚠️ {e}" for e in r["expired"]) if r["expired"] else "  ✅ Yo'q"

    r["total_sale"]  = total_sale
    r["total_vozv"]  = total_vozv
    r["net_total"]   = net_total

    # Saqlash
    data = load()
    data["reports"].append(r)
    aid = str(uid)
    if aid in data["users"]:
        data["users"][aid]["total_visits"] = data["users"][aid].get("total_visits", 0) + 1
    save(data)

    sale_txt = "\n".join(sale_lines) or "  —"
    vozv_txt = "\n".join(vozv_lines) or "  —"

    summary = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ <b>Hisobot yakunlandi!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏪 Magazin: {r.get('shop_name','')}\n"
        f"🕐 {r['started']} → {r['finished']}\n\n"
        f"📦 Sotuv:\n{sale_txt}\n"
        f"💰 Sotuv jami: <b>{fmt(total_sale)} so'm</b>\n\n"
        f"🔄 Vozvrat:\n{vozv_txt}\n"
        f"↩️ Vozvrat jami: <b>{fmt(total_vozv)} so'm</b>\n\n"
        f"💵 Sof daromad: <b>{fmt(net_total)} so'm</b>\n\n"
        f"🗑 Eskirganlar:\n{exp_txt}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    user = get_user(uid)
    bot.send_message(uid, summary, parse_mode="HTML", reply_markup=main_kb(user["role"]))

    admin_txt = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 <b>Yangi hisobot</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Agent: <b>{r['agent_name']}</b>\n"
        f"🏪 Magazin: {r.get('shop_name','')}\n"
        f"🕐 {r['started']} → {r['finished']}\n\n"
        f"📦 Sotuv:\n{sale_txt}\n"
        f"💰 Sotuv: <b>{fmt(total_sale)} so'm</b>\n\n"
        f"🔄 Vozvrat:\n{vozv_txt}\n"
        f"↩️ Vozvrat: <b>{fmt(total_vozv)} so'm</b>\n\n"
        f"💵 Sof: <b>{fmt(net_total)} so'm</b>\n\n"
        f"🗑 Eskirganlar:\n{exp_txt}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    bot.send_photo(ADMIN_ID, r["photo_id"], caption=admin_txt, parse_mode="HTML")
    bot.send_location(ADMIN_ID, r["location"]["lat"], r["location"]["lon"])

    # Supervisor va managerlarga ham yuborish
    data2 = load()
    for u_id, u in data2["users"].items():
        if u.get("role") in ("supervisor", "manager") and u.get("approved"):
            try:
                bot.send_message(int(u_id),
                    f"📋 Yangi hisobot!\n👤 {r['agent_name']}\n🏪 {r.get('shop_name','')}\n"
                    f"💰 Sotuv: {fmt(total_sale)} so'm | Sof: {fmt(net_total)} so'm",
                    parse_mode="HTML")
            except:
                pass

    sessions.pop(uid, None)

# ──────────────────────────────────────────
# HISOBOTLAR
# ──────────────────────────────────────────
def get_reports_by_period(start_date, end_date, agent_id=None):
    data = load()
    result = []
    for r in data["reports"]:
        r_date = r.get("date", r.get("started", "")[:10])
        if start_date <= r_date <= end_date:
            if agent_id is None or str(r.get("agent_id")) == str(agent_id):
                result.append(r)
    return result

def format_reports_summary(reps, title="Hisobotlar"):
    if not reps:
        return f"📭 {title}: ma'lumot yo'q."

    total_sale = sum(r.get("total_sale", 0) for r in reps)
    total_vozv = sum(r.get("total_vozv", 0) for r in reps)
    net_total  = sum(r.get("net_total", 0) for r in reps)

    product_totals = {i: 0 for i in range(len(PRODUCTS))}
    for r in reps:
        for idx, qty in r.get("product_counts", {}).items():
            product_totals[int(idx)] = product_totals.get(int(idx), 0) + qty

    prod_txt = "\n".join(
        f"  • {PRODUCTS[i]['name']}: {product_totals[i]} ta — {fmt(product_totals[i]*PRODUCTS[i]['price'])} so'm"
        for i in range(len(PRODUCTS)) if product_totals[i] > 0
    ) or "  —"

    return (
        f"📊 <b>{title}</b>\n"
        f"Jami ziyoratlar: <b>{len(reps)}</b>\n\n"
        f"📦 Mahsulotlar:\n{prod_txt}\n\n"
        f"💰 Sotuv: <b>{fmt(total_sale)} so'm</b>\n"
        f"🔄 Vozvrat: <b>{fmt(total_vozv)} so'm</b>\n"
        f"💵 Sof: <b>{fmt(net_total)} so'm</b>"
    )

def generate_excel(reps, filename="hisobot.csv"):
    """CSV format — Excel da ochiladi"""
    path = f"/tmp/{filename}"
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write("Sana,Agent,Magazin,Sotuv,Vozvrat,Sof\n")
        for r in reps:
            f.write(
                f"{r.get('date','')},{r.get('agent_name','')},"
                f"{r.get('shop_name','')},"
                f"{r.get('total_sale',0)},"
                f"{r.get('total_vozv',0)},"
                f"{r.get('net_total',0)}\n"
            )
    return path

# Agent hisobotlari
@bot.message_handler(func=lambda m: m.text == "📊 Mening hisobotlarim")
def my_reports(msg):
    uid  = msg.from_user.id
    user = get_user(uid)
    if not user or user["role"] != "agent":
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📅 Bugun", "📆 Bu oy")
    kb.add("🗓 Sana oralig'i", "📤 Excel")
    kb.add("❌ Yopish")
    sessions[uid] = {"step": "my_report_filter"}
    bot.send_message(uid, "📊 Qaysi davr uchun hisobot?",
        reply_markup=kb)

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "my_report_filter")
def my_report_filter(msg):
    uid  = msg.from_user.id
    user = get_user(uid)
    text = msg.text

    if text == "❌ Yopish":
        sessions.pop(uid, None)
        bot.send_message(uid, "✅", reply_markup=main_kb(user["role"]))
        return
    elif text == "📅 Bugun":
        reps = get_reports_by_period(today_str(), today_str(), uid)
        txt  = format_reports_summary(reps, "Bugungi hisobotlarim")
        bot.send_message(uid, txt, parse_mode="HTML")
    elif text == "📆 Bu oy":
        month_start = datetime.now().strftime("%Y-%m-01")
        reps = get_reports_by_period(month_start, today_str(), uid)
        txt  = format_reports_summary(reps, "Bu oylik hisobotlarim")
        bot.send_message(uid, txt, parse_mode="HTML")
    elif text == "📤 Excel":
        reps = get_reports_by_period("2000-01-01", today_str(), uid)
        path = generate_excel(reps, f"agent_{uid}.csv")
        with open(path, "rb") as f:
            bot.send_document(uid, f, caption="📤 Sizning hisobotlaringiz (Excel)")
    elif text == "🗓 Sana oralig'i":
        sessions[uid]["step"] = "my_date_from"
        bot.send_message(uid, "Boshlanish sanasini yozing:\n<i>Namuna: 2026-04-01</i>",
            parse_mode="HTML", reply_markup=cancel_kb())

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "my_date_from")
def my_date_from(msg):
    uid = msg.from_user.id
    try:
        datetime.strptime(msg.text.strip(), "%Y-%m-%d")
        sessions[uid]["date_from"] = msg.text.strip()
        sessions[uid]["step"] = "my_date_to"
        bot.send_message(uid, "Tugash sanasini yozing:\n<i>Namuna: 2026-04-30</i>",
            parse_mode="HTML")
    except:
        bot.send_message(uid, "❌ Format: 2026-04-01")

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "my_date_to")
def my_date_to(msg):
    uid  = msg.from_user.id
    user = get_user(uid)
    try:
        datetime.strptime(msg.text.strip(), "%Y-%m-%d")
        d_from = sessions[uid]["date_from"]
        d_to   = msg.text.strip()
        reps   = get_reports_by_period(d_from, d_to, uid)
        txt    = format_reports_summary(reps, f"{d_from} → {d_to}")
        sessions[uid]["step"] = "my_report_filter"
        bot.send_message(uid, txt, parse_mode="HTML")
    except:
        bot.send_message(uid, "❌ Format: 2026-04-30")

# ──────────────────────────────────────────
# ADMIN / SUPERVISOR / MANAGER HISOBOTLAR
# ──────────────────────────────────────────
def is_manager_or_above(uid):
    if is_admin(uid): return True
    user = get_user(uid)
    return user and user.get("approved") and user.get("role") in ("supervisor", "manager")

@bot.message_handler(func=lambda m: m.text == "📊 Hisobotlar" and is_manager_or_above(m.from_user.id))
def admin_reports(msg):
    uid = msg.from_user.id
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📅 Bugun", "📆 Bu oy")
    kb.add("👤 Agent bo'yicha", "🗓 Sana oralig'i")
    kb.add("📤 Excel yuklash", "❌ Yopish")
    sessions[uid] = {"step": "admin_report_filter"}
    bot.send_message(uid, "📊 Hisobot turi:", reply_markup=kb)

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "admin_report_filter")
def admin_report_filter(msg):
    uid  = msg.from_user.id
    user = get_user(uid)
    role = "admin" if is_admin(uid) else (user["role"] if user else "agent")
    text = msg.text

    if text == "❌ Yopish":
        sessions.pop(uid, None)
        if is_admin(uid):
            bot.send_message(uid, "✅", reply_markup=admin_kb())
        else:
            bot.send_message(uid, "✅", reply_markup=main_kb(role))
        return
    elif text == "📅 Bugun":
        reps = get_reports_by_period(today_str(), today_str())
        bot.send_message(uid, format_reports_summary(reps, "Bugungi hisobotlar"), parse_mode="HTML")
    elif text == "📆 Bu oy":
        month_start = datetime.now().strftime("%Y-%m-01")
        reps = get_reports_by_period(month_start, today_str())
        bot.send_message(uid, format_reports_summary(reps, "Bu oylik hisobotlar"), parse_mode="HTML")
    elif text == "📤 Excel yuklash":
        reps = get_reports_by_period("2000-01-01", today_str())
        path = generate_excel(reps, "barcha_hisobotlar.csv")
        with open(path, "rb") as f:
            bot.send_document(uid, f, caption="📤 Barcha hisobotlar (Excel)")
    elif text == "👤 Agent bo'yicha":
        sessions[uid]["step"] = "pick_agent"
        data = load()
        agents = [(u_id, u) for u_id, u in data["users"].items() if u.get("role") == "agent"]
        if not agents:
            bot.send_message(uid, "Hali agent yo'q.")
            return
        kb2 = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for u_id, u in agents:
            kb2.add(f"{u['name']} [{u_id}]")
        kb2.add("❌ Bekor qilish")
        sessions[uid]["agents_map"] = {f"{u['name']} [{u_id}]": u_id for u_id, u in agents}
        bot.send_message(uid, "Agentni tanlang:", reply_markup=kb2)
    elif text == "🗓 Sana oralig'i":
        sessions[uid]["step"] = "admin_date_from"
        bot.send_message(uid, "Boshlanish sanasi:\n<i>2026-04-01</i>",
            parse_mode="HTML", reply_markup=cancel_kb())

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "pick_agent")
def pick_agent(msg):
    uid  = msg.from_user.id
    text = msg.text
    agents_map = sessions[uid].get("agents_map", {})
    if text in agents_map:
        agent_uid = agents_map[text]
        reps = get_reports_by_period("2000-01-01", today_str(), agent_uid)
        bot.send_message(uid,
            format_reports_summary(reps, f"Agent: {text.split('[')[0].strip()}"),
            parse_mode="HTML")
        sessions[uid]["step"] = "admin_report_filter"
    else:
        bot.send_message(uid, "⚠️ Agentni tanlang.")

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "admin_date_from")
def admin_date_from(msg):
    uid = msg.from_user.id
    try:
        datetime.strptime(msg.text.strip(), "%Y-%m-%d")
        sessions[uid]["date_from"] = msg.text.strip()
        sessions[uid]["step"] = "admin_date_to"
        bot.send_message(uid, "Tugash sanasi:\n<i>2026-04-30</i>", parse_mode="HTML")
    except:
        bot.send_message(uid, "❌ Format: 2026-04-01")

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "admin_date_to")
def admin_date_to(msg):
    uid = msg.from_user.id
    try:
        datetime.strptime(msg.text.strip(), "%Y-%m-%d")
        d_from = sessions[uid]["date_from"]
        d_to   = msg.text.strip()
        reps   = get_reports_by_period(d_from, d_to)
        sessions[uid]["step"] = "admin_report_filter"
        bot.send_message(uid,
            format_reports_summary(reps, f"{d_from} → {d_to}"),
            parse_mode="HTML")
    except:
        bot.send_message(uid, "❌ Format: 2026-04-30")

# ──────────────────────────────────────────
# FOYDALANUVCHILAR
# ──────────────────────────────────────────
@bot.message_handler(func=lambda m: m.text == "👥 Foydalanuvchilar" and is_admin(m.from_user.id))
def admin_users(msg):
    data = load()
    if not data["users"]:
        return bot.send_message(ADMIN_ID, "Hali foydalanuvchi yo'q.")
    text = "👥 <b>Barcha foydalanuvchilar:</b>\n\n"
    for uid, u in data["users"].items():
        if str(uid) == str(ADMIN_ID): continue
        text += (f"{ROLES.get(u['role'],'')} <b>{u['name']}</b>\n"
                 f"   🆔 {uid} | 🏪 {u.get('total_visits',0)} ziyorat\n\n")
    bot.send_message(ADMIN_ID, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "👥 Agentlar" and is_manager_or_above(m.from_user.id))
def view_agents(msg):
    uid  = msg.from_user.id
    data = load()
    agents = [(u_id, u) for u_id, u in data["users"].items() if u.get("role") == "agent" and u.get("approved")]
    if not agents:
        return bot.send_message(uid, "Hali agent yo'q.")
    text = "👥 <b>Agentlar:</b>\n\n"
    for u_id, u in agents:
        reps  = [r for r in data["reports"] if str(r.get("agent_id")) == u_id]
        today = [r for r in reps if r.get("date") == today_str()]
        text += (f"👤 <b>{u['name']}</b>\n"
                 f"   🏪 Jami: {len(reps)} | 📅 Bugun: {len(today)}\n\n")
    bot.send_message(uid, text, parse_mode="HTML")

# ──────────────────────────────────────────
# REYTING
# ──────────────────────────────────────────
@bot.message_handler(func=lambda m: m.text == "🏆 Reyting" and is_manager_or_above(m.from_user.id))
def admin_rating(msg):
    uid  = msg.from_user.id
    data = load()
    scores = []
    for u_id, u in data["users"].items():
        if u.get("role") != "agent": continue
        reps   = [r for r in data["reports"] if str(r.get("agent_id")) == u_id]
        total  = sum(r.get("net_total", 0) for r in reps)
        visits = len(reps)
        scores.append((u["name"], visits, total))
    scores.sort(key=lambda x: x[2], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 <b>Agent reytingi</b>\n\n"
    for i, (name, visits, total) in enumerate(scores):
        icon = medals[i] if i < 3 else f"{i+1}."
        text += f"{icon} <b>{name}</b>\n   🏪 {visits} ziyorat | 💵 {fmt(total)} so'm\n\n"
    bot.send_message(uid, text or "Ma'lumot yo'q.", parse_mode="HTML")

# ──────────────────────────────────────────
# SOTUV STATISTIKASI
# ──────────────────────────────────────────
@bot.message_handler(func=lambda m: m.text == "💰 Sotuv statistikasi" and is_manager_or_above(m.from_user.id))
def sales_stats(msg):
    uid   = msg.from_user.id
    today = today_str()
    month = datetime.now().strftime("%Y-%m-01")
    reps_today = get_reports_by_period(today, today)
    reps_month = get_reports_by_period(month, today)

    def prod_summary(reps):
        totals = {i: 0 for i in range(len(PRODUCTS))}
        for r in reps:
            for idx, qty in r.get("product_counts", {}).items():
                totals[int(idx)] += qty
        return "\n".join(
            f"  • {PRODUCTS[i]['name']}: {totals[i]} ta — {fmt(totals[i]*PRODUCTS[i]['price'])} so'm"
            for i in range(len(PRODUCTS))
        )

    text = (
        "💰 <b>Sotuv statistikasi</b>\n\n"
        f"📅 <b>Bugun:</b>\n{prod_summary(reps_today)}\n"
        f"Jami: <b>{fmt(sum(r.get('net_total',0) for r in reps_today))} so'm</b>\n\n"
        f"📆 <b>Bu oy:</b>\n{prod_summary(reps_month)}\n"
        f"Jami: <b>{fmt(sum(r.get('net_total',0) for r in reps_month))} so'm</b>"
    )
    bot.send_message(uid, text, parse_mode="HTML")

# ──────────────────────────────────────────
# KUTAYOTGANLAR (faqat admin)
# ──────────────────────────────────────────
@bot.message_handler(func=lambda m: m.text == "⏳ Kutayotganlar" and is_admin(m.from_user.id))
def pending_list(msg):
    data = load()
    if not data.get("pending"):
        return bot.send_message(ADMIN_ID, "⏳ Kutayotgan so'rov yo'q.")
    for u_id, p in data["pending"].items():
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{u_id}_{p['role']}"),
            types.InlineKeyboardButton("❌ Rad etish",  callback_data=f"reject_{u_id}"),
        )
        bot.send_message(ADMIN_ID,
            f"⏳ <b>Kutayotgan so'rov</b>\n\n"
            f"👤 {p['name']}\n🆔 {u_id}\n🎭 {ROLES.get(p['role'],'')}\n📅 {p['time']}",
            parse_mode="HTML", reply_markup=kb)

print("✅ Bot ishga tushdi...")
bot.infinity_polling()
