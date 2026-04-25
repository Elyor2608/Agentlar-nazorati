"""
🤖 Agent Nazorat Boti - To'liq versiya
=======================================
Ketma-ketlik:
1. Lokatsiya yuborish
2. Foto + izoh
3. Mahsulot miqdori
4. Eskirgan mahsulotlar
5. Yakun hisobot

O'rnatish:
  pip install pyTelegramBotAPI

Ishga tushirish:
  python agent_bot.py
"""

import telebot
from telebot import types
from datetime import datetime
import json, os

# =============================================
# ⚙️  SOZLAMALAR
# =============================================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"   # @BotFather dan oling
ADMIN_ID  = 123456789               # Sizning ID: https://t.me/userinfobot
# =============================================

bot       = telebot.TeleBot(BOT_TOKEN)
DATA_FILE = "agents_data.json"

# Har bir agent uchun joriy sessiya holati xotirada saqlanadi
sessions = {}   # { user_id: { "step": ..., "report": {...} } }

# ──────────────────────────────────────────
# 🗄  Ma'lumotlar
# ──────────────────────────────────────────
def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"agents": {}, "reports": []}

def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_agent(uid):
    return load()["agents"].get(str(uid))

def is_admin(uid):
    return uid == ADMIN_ID

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

# ──────────────────────────────────────────
# 🛠  Yordamchi: klaviatura
# ──────────────────────────────────────────
def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🏪 Magazin ziyoratini boshlash")
    kb.add("📊 Mening hisobotlarim")
    return kb

def location_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📍 Lokatsiyani yuborish", request_location=True))
    kb.add("❌ Bekor qilish")
    return kb

def cancel_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("❌ Bekor qilish")
    return kb

# ──────────────────────────────────────────
# 🚀  /start
# ──────────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    uid = msg.from_user.id
    if is_admin(uid):
        return admin_panel(msg)

    agent = get_agent(uid)
    if agent:
        bot.send_message(uid,
            f"👋 Xush kelibsiz, <b>{agent['name']}</b>!\n"
            "Yangi ziyorat boshlash uchun tugmani bosing.",
            parse_mode="HTML", reply_markup=main_keyboard())
    else:
        bot.send_message(uid,
            "👋 Salom! Botdan foydalanish uchun ismingizni yuboring:")
        bot.register_next_step_handler(msg, step_register)

# ──────────────────────────────────────────
# 📝  Ro'yxatdan o'tish
# ──────────────────────────────────────────
def step_register(msg):
    uid  = msg.from_user.id
    name = msg.text.strip()
    data = load()
    data["agents"][str(uid)] = {
        "name"         : name,
        "username"     : msg.from_user.username or "",
        "registered"   : now_str(),
        "total_visits" : 0,
    }
    save(data)
    bot.send_message(uid,
        f"✅ Ro'yxatdan o'tdingiz, <b>{name}</b>!",
        parse_mode="HTML", reply_markup=main_keyboard())
    bot.send_message(ADMIN_ID,
        f"🆕 Yangi agent!\n👤 {name}\n🆔 {uid}\n📅 {now_str()}")

# ──────────────────────────────────────────
# 🏪  Ziyoratni boshlash
# ──────────────────────────────────────────
@bot.message_handler(func=lambda m: m.text == "🏪 Magazin ziyoratini boshlash")
def start_visit(msg):
    uid   = msg.from_user.id
    agent = get_agent(uid)
    if not agent:
        return bot.send_message(uid, "❌ Avval /start bosing.")

    sessions[uid] = {"step": "location", "report": {
        "agent_id"  : uid,
        "agent_name": agent["name"],
        "started"   : now_str(),
    }}
    bot.send_message(uid,
        "📍 <b>1-qadam: Lokatsiya</b>\n\n"
        "Hozirgi joylashuvingizni yuboring:",
        parse_mode="HTML", reply_markup=location_keyboard())

# ──────────────────────────────────────────
# ❌  Bekor qilish
# ──────────────────────────────────────────
@bot.message_handler(func=lambda m: m.text == "❌ Bekor qilish")
def cancel(msg):
    uid = msg.from_user.id
    sessions.pop(uid, None)
    bot.send_message(uid, "🚫 Bekor qilindi.", reply_markup=main_keyboard())

# ──────────────────────────────────────────
# 📍  QADAM 1 — Lokatsiya
# ──────────────────────────────────────────
@bot.message_handler(content_types=["location"])
def receive_location(msg):
    uid = msg.from_user.id
    sess = sessions.get(uid)
    if not sess or sess["step"] != "location":
        return

    lat = msg.location.latitude
    lon = msg.location.longitude
    sess["report"]["location"] = {"lat": lat, "lon": lon}
    sess["step"] = "photo"

    bot.send_message(uid,
        f"✅ Lokatsiya qabul qilindi!\n"
        f"📌 {lat:.5f}, {lon:.5f}\n\n"
        "📸 <b>2-qadam: Foto hisobot</b>\n\n"
        "Magazin yoki javondan <b>foto yuboring</b>:",
        parse_mode="HTML", reply_markup=cancel_keyboard())

# ──────────────────────────────────────────
# 📸  QADAM 2 — Foto
# ──────────────────────────────────────────
@bot.message_handler(content_types=["photo"])
def receive_photo(msg):
    uid  = msg.from_user.id
    sess = sessions.get(uid)
    if not sess or sess["step"] != "photo":
        return

    sess["report"]["photo_id"] = msg.photo[-1].file_id
    sess["step"] = "comment"

    bot.send_message(uid,
        "✅ Foto qabul qilindi!\n\n"
        "💬 <b>Izoh yozing</b> (magazin nomi, holati, muammo bo'lsa yozing):",
        parse_mode="HTML", reply_markup=cancel_keyboard())

# ──────────────────────────────────────────
# 💬  QADAM 3 — Izoh
# ──────────────────────────────────────────
@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "comment")
def receive_comment(msg):
    uid  = msg.from_user.id
    sess = sessions[uid]
    sess["report"]["comment"] = msg.text.strip()
    sess["step"] = "products"

    bot.send_message(uid,
        "✅ Izoh qabul qilindi!\n\n"
        "📦 <b>3-qadam: Mahsulotlar</b>\n\n"
        "Qaysi mahsulotdan nechta berdingiz?\n"
        "<i>Namuna: Pepsi 0.5L - 10 ta, Sprite 1L - 5 ta</i>\n\n"
        "Har bir mahsulotni alohida qatorda yozing:",
        parse_mode="HTML", reply_markup=cancel_keyboard())

# ──────────────────────────────────────────
# 📦  QADAM 4 — Mahsulotlar
# ──────────────────────────────────────────
@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "products")
def receive_products(msg):
    uid  = msg.from_user.id
    sess = sessions[uid]

    lines = [l.strip() for l in msg.text.strip().splitlines() if l.strip()]
    sess["report"]["products"] = lines
    sess["step"] = "expired"

    bot.send_message(uid,
        f"✅ {len(lines)} ta mahsulot kiritildi!\n\n"
        "🗑 <b>4-qadam: Eskirgan mahsulotlar</b>\n\n"
        "Muddati o'tgan mahsulotlarni kiriting.\n"
        "<i>Namuna: Lipton choy 12.2025 - 3 ta</i>\n\n"
        "Eskirgan mahsulot bo'lmasa — <b>Yo'q</b> deb yozing:",
        parse_mode="HTML", reply_markup=cancel_keyboard())

# ──────────────────────────────────────────
# 🗑  QADAM 5 — Eskirgan mahsulotlar
# ──────────────────────────────────────────
@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "expired")
def receive_expired(msg):
    uid  = msg.from_user.id
    sess = sessions[uid]
    text = msg.text.strip()

    if text.lower() in ["yo'q", "yoq", "нет", "no", "-"]:
        sess["report"]["expired"] = []
    else:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        sess["report"]["expired"] = lines

    sess["report"]["finished"] = now_str()
    sess["step"] = "done"

    # Hisobotni saqlash
    data = load()
    data["reports"].append(sess["report"])
    aid = str(uid)
    if aid in data["agents"]:
        data["agents"][aid]["total_visits"] = data["agents"][aid].get("total_visits", 0) + 1
    save(data)

    # ── Agent uchun yakun xabar
    r        = sess["report"]
    prod_txt = "\n".join(f"  • {p}" for p in r["products"]) or "  —"
    exp_txt  = "\n".join(f"  ⚠️ {e}" for e in r["expired"]) if r["expired"] else "  ✅ Yo'q"

    summary = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ <b>Hisobot yakunlandi!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {r['started']} → {r['finished']}\n"
        f"📌 Lokatsiya: {r['location']['lat']:.4f}, {r['location']['lon']:.4f}\n"
        f"💬 Izoh: {r['comment']}\n\n"
        f"📦 Berilgan mahsulotlar:\n{prod_txt}\n\n"
        f"🗑 Eskirgan mahsulotlar:\n{exp_txt}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    bot.send_message(uid, summary, parse_mode="HTML", reply_markup=main_keyboard())

    # ── Adminga yuborish
    admin_txt = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 <b>Yangi hisobot</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Agent: <b>{r['agent_name']}</b> (ID: {uid})\n"
        f"🕐 {r['started']} → {r['finished']}\n"
        f"💬 Izoh: {r['comment']}\n\n"
        f"📦 Mahsulotlar:\n{prod_txt}\n\n"
        f"🗑 Eskirganlar:\n{exp_txt}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    # Foto
    bot.send_photo(ADMIN_ID, r["photo_id"], caption=admin_txt, parse_mode="HTML")
    # Lokatsiya
    bot.send_location(ADMIN_ID, r["location"]["lat"], r["location"]["lon"])

    sessions.pop(uid, None)

# ──────────────────────────────────────────
# 📊  Agent o'z hisobotlari
# ──────────────────────────────────────────
@bot.message_handler(func=lambda m: m.text == "📊 Mening hisobotlarim")
def my_reports(msg):
    uid   = msg.from_user.id
    data  = load()
    agent = get_agent(uid)
    if not agent:
        return bot.send_message(uid, "❌ /start bosing.")

    my = [r for r in data["reports"] if r.get("agent_id") == uid]
    total = len(my)
    total_products = sum(len(r.get("products", [])) for r in my)
    total_expired  = sum(len(r.get("expired", [])) for r in my)

    bot.send_message(uid,
        f"📊 <b>Sizning statistikangiz</b>\n\n"
        f"🏪 Jami ziyoratlar: <b>{total}</b>\n"
        f"📦 Jami mahsulot qatorlari: <b>{total_products}</b>\n"
        f"🗑 Jami eskirgan mahsulotlar: <b>{total_expired}</b>",
        parse_mode="HTML")

# ──────────────────────────────────────────
# 👑  ADMIN PANEL
# ──────────────────────────────────────────
def admin_panel(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👥 Agentlar ro'yxati", "📊 Bugungi hisobotlar")
    kb.add("🏆 Reyting")
    bot.send_message(ADMIN_ID,
        "👑 <b>Admin panel</b>\nXush kelibsiz!",
        parse_mode="HTML", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "👥 Agentlar ro'yxati" and is_admin(m.from_user.id))
def admin_agents(msg):
    data   = load()
    agents = data["agents"]
    if not agents:
        return bot.send_message(ADMIN_ID, "Hali agent yo'q.")

    text = "👥 <b>Barcha agentlar:</b>\n\n"
    for uid, a in agents.items():
        text += (f"👤 <b>{a['name']}</b>\n"
                 f"   🆔 {uid}\n"
                 f"   🏪 Ziyoratlar: {a.get('total_visits', 0)}\n"
                 f"   📅 Ro'yxat: {a['registered']}\n\n")
    bot.send_message(ADMIN_ID, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "📊 Bugungi hisobotlar" and is_admin(m.from_user.id))
def admin_today(msg):
    data  = load()
    today = datetime.now().strftime("%Y-%m-%d")
    reps  = [r for r in data["reports"] if r.get("started", "").startswith(today)]

    if not reps:
        return bot.send_message(ADMIN_ID, f"📭 Bugun ({today}) hali hisobot yo'q.")

    text = f"📊 <b>Bugungi hisobotlar ({today})</b>\n<b>{len(reps)} ta ziyorat</b>\n\n"
    for r in reps:
        prod_txt = ", ".join(r.get("products", [])) or "—"
        exp_txt  = ", ".join(r.get("expired", [])) or "yo'q"
        text += (f"👤 <b>{r['agent_name']}</b> — {r['started']}\n"
                 f"   💬 {r.get('comment','')}\n"
                 f"   📦 {prod_txt}\n"
                 f"   🗑 {exp_txt}\n\n")
    bot.send_message(ADMIN_ID, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🏆 Reyting" and is_admin(m.from_user.id))
def admin_rating(msg):
    data   = load()
    agents = data["agents"]
    reps   = data["reports"]

    scores = {}
    for uid, a in agents.items():
        visits = sum(1 for r in reps if str(r.get("agent_id")) == uid)
        scores[uid] = (a["name"], visits)

    sorted_agents = sorted(scores.values(), key=lambda x: x[1], reverse=True)
    medals = ["🥇", "🥈", "🥉"]

    text = "🏆 <b>Agent reytingi (ziyorat soni bo'yicha)</b>\n\n"
    for i, (name, visits) in enumerate(sorted_agents):
        icon = medals[i] if i < 3 else f"{i+1}."
        text += f"{icon} <b>{name}</b> — {visits} ta ziyorat\n"

    bot.send_message(ADMIN_ID, text, parse_mode="HTML")

# ──────────────────────────────────────────
# ▶️  ISHGA TUSHIRISH
# ──────────────────────────────────────────
print("✅ Bot ishga tushdi...")
bot.infinity_polling()
