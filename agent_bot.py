"""
🤖 Bot 3.2 - Mijozlar bazasi + Qidiruv + Lokatsiya
"""

import telebot
from telebot import types
from datetime import datetime, date, timedelta
import json, os, time, math

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

bot          = telebot.TeleBot(BOT_TOKEN)
DATA_FILE    = "bot_data.json"
SHOPS_FILE   = "shops.json"
CLIENTS_FILE = "clients.json"
sessions     = {}

# =============================================
# 🗄 MA'LUMOTLAR
# =============================================
def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "reports": [], "pending": {}}

def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_shops():
    if os.path.exists(SHOPS_FILE):
        with open(SHOPS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def save_shops(shops):
    with open(SHOPS_FILE, "w", encoding="utf-8") as f:
        json.dump(shops, f, ensure_ascii=False, indent=2)

def load_clients():
    if os.path.exists(CLIENTS_FILE):
        with open(CLIENTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def save_clients(clients):
    with open(CLIENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)

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

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# =============================================
# 🏪 MAGAZINLAR
# =============================================
def find_nearby_shops(lat, lon, radius=100):
    shops = load_shops()
    nearby = []
    for shop in shops:
        dist = haversine(lat, lon, shop["lat"], shop["lon"])
        if dist <= radius:
            shop["distance"] = int(dist)
            nearby.append(shop)
    nearby.sort(key=lambda x: x["distance"])
    return nearby

def add_shop(name, lat, lon):
    shops = load_shops()
    for s in shops:
        if s["name"].lower() == name.lower() and haversine(lat, lon, s["lat"], s["lon"]) < 50:
            return s
    shop = {"id": len(shops) + 1, "name": name, "lat": lat, "lon": lon, "created": now_str()}
    shops.append(shop)
    save_shops(shops)
    return shop

# =============================================
# 👥 MIJOZLAR
# =============================================
def add_client(name, address, phone, lat=None, lon=None):
    clients = load_clients()
    client = {
        "id": len(clients) + 1,
        "name": name,
        "address": address,
        "phone": phone,
        "lat": lat,
        "lon": lon,
        "created": now_str()
    }
    clients.append(client)
    save_clients(clients)
    return client

def search_clients(query):
    clients = load_clients()
    query = query.lower()
    return [c for c in clients if query in c["name"].lower() or query in c.get("address","").lower()]

# =============================================
# KLAVIATURALAR
# =============================================
def main_kb(role):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if role == "agent":
        kb.add("🛒 Savdoni boshlash")
        kb.add("📊 Mening hisobotlarim")
        kb.add("👥 Mijozlar")
    elif role in ("supervisor", "manager"):
        kb.add("📊 Hisobotlar", "👥 Agentlar")
        kb.add("💰 Sotuv statistikasi", "🏆 Reyting")
        kb.add("🏪 Magazinlar", "👥 Mijozlar")
    return kb

def admin_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📊 Hisobotlar", "👥 Foydalanuvchilar")
    kb.add("💰 Sotuv statistikasi", "🏆 Reyting")
    kb.add("🏪 Magazinlar", "👥 Mijozlar")
    kb.add("⏳ Kutayotganlar")
    return kb

def back_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⬅️ Orqaga")
    return kb

def location_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📍 Lokatsiyani yuborish", request_location=True))
    kb.add("⬅️ Orqaga")
    return kb

def products_kb(counts):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i, p in enumerate(PRODUCTS):
        cnt = counts.get(str(i), 0)
        label = f"{p['name']} [{cnt} ta]" if cnt > 0 else p['name']
        kb.add(label)
    kb.add("✅ Tayyor", "⬅️ Orqaga")
    return kb

def qty_numpad_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("1️⃣", "2️⃣", "3️⃣")
    kb.row("4️⃣", "5️⃣", "6️⃣")
    kb.row("7️⃣", "8️⃣", "9️⃣")
    kb.row("✅ Tasdiqlash", "0️⃣", "🔙")
    kb.add("⬅️ Orqaga")
    return kb

# =============================================
# /START
# =============================================
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    uid = msg.from_user.id
    if is_admin(uid):
        data = load()
        if str(uid) not in data["users"]:
            data["users"][str(uid)] = {"name": "Admin", "role": "admin", "registered": now_str(), "approved": True}
            save(data)
        return bot.send_message(uid, "👑 <b>Admin panel</b>\nXush kelibsiz!", parse_mode="HTML", reply_markup=admin_kb())
    user = get_user(uid)
    if user:
        if not user.get("approved"):
            return bot.send_message(uid, "⏳ So'rovingiz hali tasdiqlanmagan.")
        bot.send_message(uid, f"👋 Xush kelibsiz, <b>{user['name']}</b>! ({ROLES.get(user['role'],'')})", parse_mode="HTML", reply_markup=main_kb(user["role"]))
    else:
        bot.send_message(uid, "👋 Salom! Botdan foydalanish uchun <b>Ism Familiyangizni</b> yuboring:", parse_mode="HTML")
        sessions[uid] = {"step": "register_name"}

# =============================================
# RO'YXATDAN O'TISH
# =============================================
@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "register_name")
def register_name(msg):
    uid, name = msg.from_user.id, msg.text.strip()
    sessions[uid] = {"step": "register_role", "name": name}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👤 Agent", "🔷 Supervayzor", "🔶 Menejer")
    bot.send_message(uid, f"Ismingiz: <b>{name}</b>\n\nXodimni tanlang:", parse_mode="HTML", reply_markup=kb)

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "register_role")
def register_role(msg):
    uid, text = msg.from_user.id, msg.text.strip()
    role_map = {"👤 Agent": "agent", "🔷 Supervayzor": "supervisor", "🔶 Menejer": "manager"}
    if text not in role_map: return bot.send_message(uid, "⚠️ Tugmalardan birini bosing.")
    role, name = role_map[text], sessions[uid]["name"]
    sessions.pop(uid, None)
    data = load()
    data["pending"][str(uid)] = {"uid": uid, "name": name, "role": role, "username": msg.from_user.username or "", "time": now_str()}
    save(data)
    bot.send_message(uid, "✅ So'rovingiz yuborildi!\n\n⏳ Admin tasdiqlashini kuting.", reply_markup=types.ReplyKeyboardRemove())
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{uid}_{role}"), types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{uid}"))
    bot.send_message(ADMIN_ID, f"🆕 <b>Yangi so'rov</b>\n\n👤 {name}\n🆔 {uid}\n🎭 {ROLES[role]}\n📅 {now_str()}", parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("approve_"))
def approve_user(call):
    _, uid, role = call.data.split("_"); uid = int(uid)
    data = load(); p = data["pending"].get(str(uid))
    if not p: return bot.answer_callback_query(call.id, "Topilmadi!")
    data["users"][str(uid)] = {"name": p["name"], "role": role, "username": p.get("username",""), "registered": p["time"], "approved": True, "total_visits": 0}
    data["pending"].pop(str(uid), None); save(data)
    bot.answer_callback_query(call.id, "✅"); bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, f"✅ <b>{p['name']}</b> tasdiqlandi!", parse_mode="HTML")
    try: bot.send_message(uid, f"🎉 Tabriklaymiz, <b>{p['name']}</b>!\n\nXodim: {ROLES[role]}", parse_mode="HTML", reply_markup=main_kb(role))
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("reject_"))
def reject_user(call):
    uid = int(call.data.split("_")[1]); data = load(); p = data["pending"].get(str(uid))
    if not p: return bot.answer_callback_query(call.id, "Topilmadi!")
    data["pending"].pop(str(uid), None); save(data)
    bot.answer_callback_query(call.id, "❌"); bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, f"❌ <b>{p['name']}</b> rad etildi.", parse_mode="HTML")
    try: bot.send_message(uid, "❌ So'rovingiz rad etildi.")
    except: pass

# =============================================
# ⬅️ ORQAGA
# =============================================
@bot.message_handler(func=lambda m: m.text == "⬅️ Orqaga")
def go_back(msg):
    uid = msg.from_user.id; sess = sessions.get(uid, {}); user = get_user(uid)
    if not sess or sess.get("step") is None:
        if user and user.get("approved"):
            kb = admin_kb() if is_admin(uid) else main_kb(user["role"])
            return bot.send_message(uid, "↩️", reply_markup=kb)
        return
    step = sess.get("step", "")
    if step in ("location", "shop_select", "new_shop"):
        sessions.pop(uid, None)
        bot.send_message(uid, "↩️ Bekor qilindi.", reply_markup=main_kb(user["role"]))
    elif step == "photo":
        sess["step"] = "location"
        bot.send_message(uid, "📍 <b>1-qadam: Lokatsiya</b>", parse_mode="HTML", reply_markup=location_kb())
    elif step == "products":
        sess["step"] = "photo"
        bot.send_message(uid, "📸 <b>2-qadam: Foto</b>", parse_mode="HTML", reply_markup=back_kb())
    elif step == "vozvrat":
        sess["step"] = "products"
        bot.send_message(uid, "📦 <b>3-qadam: Mahsulotlar</b>", parse_mode="HTML", reply_markup=products_kb(sess["report"].get("product_counts", {})))
    elif step in ("client_menu","client_search","client_add_name","client_add_address","client_add_phone","client_add_location","client_detail"):
        sessions.pop(uid, None)
        kb = admin_kb() if is_admin(uid) else main_kb(user["role"])
        bot.send_message(uid, "↩️", reply_markup=kb)
    elif step in ("my_report_menu","admin_report_menu","pick_agent","admin_date_from","admin_date_to","my_date_from","my_date_to","pick_product","pick_shop"):
        sessions.pop(uid, None)
        kb = admin_kb() if is_admin(uid) else main_kb(user["role"])
        bot.send_message(uid, "↩️", reply_markup=kb)

# =============================================
# 👥 MIJOZLAR BO'LIMI
# =============================================
@bot.message_handler(func=lambda m: m.text == "👥 Mijozlar")
def clients_main(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    if not user or not user.get("approved"): return bot.send_message(uid, "❌ Ruxsat yo'q.")
    show_client_menu(uid)

def show_client_menu(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔍 Mijoz qidirish", "➕ Yangi mijoz")
    kb.add("📋 Barcha mijozlar")
    kb.add("⬅️ Orqaga")
    sessions[uid] = {"step": "client_menu"}
    bot.send_message(uid, "👥 <b>Mijozlar bo'limi</b>\n\nTanlang:", parse_mode="HTML", reply_markup=kb)

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "client_menu")
def client_menu_handler(msg):
    uid, text = msg.from_user.id, msg.text
    if text == "⬅️ Orqaga":
        sessions.pop(uid, None)
        user = get_user(uid)
        kb = admin_kb() if is_admin(uid) else main_kb(user["role"])
        return bot.send_message(uid, "↩️", reply_markup=kb)
    elif text == "📋 Barcha mijozlar":
        show_all_clients(uid)
    elif text == "🔍 Mijoz qidirish":
        sessions[uid]["step"] = "client_search"
        bot.send_message(uid, "🔍 <b>Mijoz qidirish</b>\n\nMijoz nomi yoki adresini yozing:", parse_mode="HTML", reply_markup=back_kb())
    elif text == "➕ Yangi mijoz":
        start_add_client(uid)

# --- Barcha mijozlar ---
def show_all_clients(uid, page=0):
    clients = load_clients()
    if not clients: return bot.send_message(uid, "👥 Hali mijoz yo'q.\n➕ Yangi mijoz qo'shing!")
    per_page = 10; total = len(clients); pages = (total + per_page - 1) // per_page
    start, end = page * per_page, min((page + 1) * per_page, total)
    text = f"👥 <b>Mijozlar</b> ({start+1}-{end} / {total})\n\n"
    for c in clients[start:end]:
        text += f"  🆔 {c['id']}. <b>{c['name']}</b>\n"
        text += f"     📍 {c.get('address','—')}\n"
        text += f"     📞 {c.get('phone','—')}\n\n"
    kb = types.InlineKeyboardMarkup()
    if page > 0: kb.add(types.InlineKeyboardButton("◀️ Oldingi", callback_data=f"clients_page_{page-1}"))
    if end < total: kb.add(types.InlineKeyboardButton("Keyingi ▶️", callback_data=f"clients_page_{page+1}"))
    kb.add(types.InlineKeyboardButton("📍 Lokatsiyasini ko'rish", callback_data=f"client_map_select"))
    bot.send_message(uid, text, parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("clients_page_"))
def clients_page(call):
    page = int(call.data.split("_")[2])
    show_all_clients(call.from_user.id, page)
    bot.answer_callback_query(call.id)

# --- Qidiruv ---
@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "client_search")
def client_search(msg):
    uid, query = msg.from_user.id, msg.text.strip()
    if query == "⬅️ Orqaga": return show_client_menu(uid)
    results = search_clients(query)
    if not results:
        return bot.send_message(uid, f"🔍 <b>'{query}'</b> bo'yicha hech narsa topilmadi.\n\nBoshqa nom yozing:", parse_mode="HTML", reply_markup=back_kb())
    text = f"🔍 <b>'{query}'</b> bo'yicha natijalar: <b>{len(results)} ta</b>\n\n"
    for c in results:
        text += f"  🆔 {c['id']}. <b>{c['name']}</b>\n"
        text += f"     📍 {c.get('address','—')}\n"
        text += f"     📞 {c.get('phone','—')}\n\n"
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔍 Boshqa qidirish")
    if any(c.get("lat") for c in results):
        kb.add("📍 Lokatsiyasini ko'rish")
    kb.add("📋 Barcha mijozlar", "⬅️ Orqaga")
    sessions[uid]["search_results"] = results
    sessions[uid]["step"] = "client_search_result"
    bot.send_message(uid, text, parse_mode="HTML", reply_markup=kb)

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "client_search_result")
def client_search_result_handler(msg):
    uid, text = msg.from_user.id, msg.text
    if text == "⬅️ Orqaga": return show_client_menu(uid)
    if text == "📋 Barcha mijozlar": return show_all_clients(uid)
    if text == "🔍 Boshqa qidirish":
        sessions[uid]["step"] = "client_search"
        return bot.send_message(uid, "🔍 Mijoz nomi yoki adresini yozing:", parse_mode="HTML", reply_markup=back_kb())
    if text == "📍 Lokatsiyasini ko'rish":
        results = sessions[uid].get("search_results", [])
        with_loc = [c for c in results if c.get("lat")]
        if not with_loc: return bot.send_message(uid, "📍 Bu mijozlar uchun lokatsiya kiritilmagan.")
        for c in with_loc:
            bot.send_location(uid, c["lat"], c["lon"])
            bot.send_message(uid, f"📍 <b>{c['name']}</b>\n{c.get('address','')}", parse_mode="HTML")
        return
    # Mijoz ID sini qidirish
    for c in sessions[uid].get("search_results", []):
        if text.strip() == str(c["id"]) or text.strip() == c["name"]:
            show_client_detail(uid, c)
            return
    bot.send_message(uid, "⚠️ Mijozni tanlang yoki tugmalardan foydalaning.")

# --- Mijoz kartasi ---
def show_client_detail(uid, client):
    sessions[uid] = {"step": "client_detail", "client": client}
    text = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Mijoz kartasi</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: {client['id']}\n"
        f"👤 Nomi: <b>{client['name']}</b>\n"
        f"📍 Adres: {client.get('address','—')}\n"
        f"📞 Tel: {client.get('phone','—')}\n"
        f"📅 Qo'shilgan: {client.get('created','—')}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if client.get("lat"):
        kb.add("📍 Lokatsiyani ko'rish")
    kb.add("🔍 Boshqa qidirish", "⬅️ Orqaga")
    bot.send_message(uid, text, parse_mode="HTML", reply_markup=kb)

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "client_detail")
def client_detail_handler(msg):
    uid, text = msg.from_user.id, msg.text
    if text == "⬅️ Orqaga": return show_client_menu(uid)
    if text == "🔍 Boshqa qidirish":
        sessions[uid]["step"] = "client_search"
        return bot.send_message(uid, "🔍 Mijoz nomi yoki adresini yozing:", parse_mode="HTML", reply_markup=back_kb())
    if text == "📍 Lokatsiyani ko'rish":
        client = sessions[uid].get("client", {})
        if client.get("lat"):
            bot.send_location(uid, client["lat"], client["lon"])
            bot.send_message(uid, f"📍 <b>{client['name']}</b>\n{client.get('address','')}", parse_mode="HTML")
        else:
            bot.send_message(uid, "📍 Lokatsiya kiritilmagan.")
        return
    show_client_menu(uid)

# --- Yangi mijoz qo'shish ---
def start_add_client(uid):
    sessions[uid] = {"step": "client_add_name", "new_client": {}}
    bot.send_message(uid, "➕ <b>Yangi mijoz</b>\n\n1️⃣ Mijoz nomini yozing:", parse_mode="HTML", reply_markup=back_kb())

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "client_add_name")
def client_add_name(msg):
    uid, text = msg.from_user.id, msg.text.strip()
    if text == "⬅️ Orqaga": return show_client_menu(uid)
    if len(text) < 2: return bot.send_message(uid, "⚠️ Kamida 2 belgi yozing!")
    sessions[uid]["new_client"]["name"] = text
    sessions[uid]["step"] = "client_add_address"
    bot.send_message(uid, f"✅ Nomi: <b>{text}</b>\n\n2️⃣ Adresini yozing:", parse_mode="HTML", reply_markup=back_kb())

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "client_add_address")
def client_add_address(msg):
    uid, text = msg.from_user.id, msg.text.strip()
    if text == "⬅️ Orqaga":
        sessions[uid]["step"] = "client_add_name"
        return bot.send_message(uid, "1️⃣ Mijoz nomini yozing:", parse_mode="HTML", reply_markup=back_kb())
    sessions[uid]["new_client"]["address"] = text
    sessions[uid]["step"] = "client_add_phone"
    bot.send_message(uid, f"✅ Adres: <b>{text}</b>\n\n3️⃣ Tel raqamini yozing:", parse_mode="HTML", reply_markup=back_kb())

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "client_add_phone")
def client_add_phone(msg):
    uid, text = msg.from_user.id, msg.text.strip()
    if text == "⬅️ Orqaga":
        sessions[uid]["step"] = "client_add_address"
        return bot.send_message(uid, "2️⃣ Adresini yozing:", parse_mode="HTML", reply_markup=back_kb())
    sessions[uid]["new_client"]["phone"] = text
    sessions[uid]["step"] = "client_add_location"
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📍 Lokatsiyani yuborish", request_location=True))
    kb.add("⏭ O'tkazib yuborish", "⬅️ Orqaga")
    bot.send_message(uid, f"✅ Tel: <b>{text}</b>\n\n4️⃣ Lokatsiyani yuboring yoki o'tkazib yuboring:", parse_mode="HTML", reply_markup=kb)

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "client_add_location")
def client_add_location(msg):
    uid = msg.from_user.id
    if msg.text == "⬅️ Orqaga":
        sessions[uid]["step"] = "client_add_phone"
        return bot.send_message(uid, "3️⃣ Tel raqamini yozing:", parse_mode="HTML", reply_markup=back_kb())
    if msg.text == "⏭ O'tkazib yuborish":
        nc = sessions[uid]["new_client"]
        client = add_client(nc["name"], nc["address"], nc["phone"])
        sessions.pop(uid, None)
        bot.send_message(uid, f"✅ Mijoz saqlandi!\n\n👤 <b>{client['name']}</b>\n📍 {client['address']}\n📞 {client['phone']}", parse_mode="HTML")
        return show_client_menu(uid)
    if msg.location:
        nc = sessions[uid]["new_client"]
        client = add_client(nc["name"], nc["address"], nc["phone"], msg.location.latitude, msg.location.longitude)
        sessions.pop(uid, None)
        bot.send_location(uid, client["lat"], client["lon"])
        bot.send_message(uid, f"✅ Mijoz lokatsiya bilan saqlandi!\n\n👤 <b>{client['name']}</b>\n📍 {client['address']}\n📞 {client['phone']}", parse_mode="HTML")
        return show_client_menu(uid)
    bot.send_message(uid, "⚠️ Lokatsiya yuboring yoki 'O'tkazib yuborish' bosing.")

# --- Lokatsiyani ko'rish (callback) ---
@bot.callback_query_handler(func=lambda c: c.data == "client_map_select")
def client_map_select(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    bot.send_message(uid, "📍 Qaysi mijozning lokatsiyasini ko'rmoqchisiz?\nMijoz ID sini yoki nomini yozing:", reply_markup=back_kb())
    sessions[uid] = {"step": "client_map_input"}

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "client_map_input")
def client_map_input(msg):
    uid, text = msg.from_user.id, msg.text.strip()
    if text == "⬅️ Orqaga": return show_client_menu(uid)
    clients = load_clients()
    found = None
    for c in clients:
        if str(c.get("id")) == text or c.get("name","").lower() == text.lower():
            found = c; break
    if not found: return bot.send_message(uid, "❌ Topilmadi. Boshqa ID yoki nom yozing:", reply_markup=back_kb())
    if not found.get("lat"): return bot.send_message(uid, f"📍 <b>{found['name']}</b> uchun lokatsiya kiritilmagan.", parse_mode="HTML")
    bot.send_location(uid, found["lat"], found["lon"])
    bot.send_message(uid, f"📍 <b>{found['name']}</b>\n{found.get('address','')}", parse_mode="HTML")
    sessions.pop(uid, None)
    show_client_menu(uid)

# =============================================
# 🛒 SAVDONI BOSHLASH
# =============================================
@bot.message_handler(func=lambda m: m.text == "🛒 Savdoni boshlash")
def start_visit(msg):
    uid = msg.from_user.id; user = get_user(uid)
    if not user or not user.get("approved") or user["role"] != "agent":
        return bot.send_message(uid, "❌ Ruxsat yo'q.")
    sessions[uid] = {"step": "location", "report": {"agent_id": uid, "agent_name": user["name"], "started": now_str(), "date": today_str()}}
    bot.send_message(uid, "📍 <b>1-qadam: Lokatsiya</b>\n\nHozirgi joylashuvingizni yuboring:", parse_mode="HTML", reply_markup=location_kb())

@bot.message_handler(content_types=["location"])
def receive_location(msg):
    uid = msg.from_user.id; sess = sessions.get(uid)
    if not sess or sess["step"] != "location": return
    lat, lon = msg.location.latitude, msg.location.longitude
    sess["report"]["location"] = {"lat": lat, "lon": lon}
    nearby = find_nearby_shops(lat, lon, 100)
    if nearby:
        sess["step"] = "shop_select"; sess["nearby_shops"] = nearby
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for s in nearby: kb.add(f"🏪 {s['name']} ({s['distance']}m)")
        kb.add("🆕 Yangi magazin", "⬅️ Orqaga")
        bot.send_message(uid, f"✅ Lokatsiya qabul qilindi!\n\n📡 100m ichidagi magazinlar:\nTanlang:", parse_mode="HTML", reply_markup=kb)
    else:
        sess["step"] = "new_shop"
        bot.send_message(uid, "✅ Lokatsiya qabul qilindi!\n\n📡 Yaqinda magazin topilmadi.\n🆕 <b>Yangi magazin nomini yozing:</b>", parse_mode="HTML", reply_markup=back_kb())

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "shop_select")
def select_shop(msg):
    uid, sess, text = msg.from_user.id, sessions[uid], msg.text
    if text == "⬅️ Orqaga": sessions.pop(uid, None); return bot.send_message(uid, "↩️", reply_markup=main_kb(get_user(uid)["role"]))
    if text == "🆕 Yangi magazin": sess["step"] = "new_shop"; return bot.send_message(uid, "🏪 Yangi magazin nomini yozing:", reply_markup=back_kb())
    for s in sess.get("nearby_shops", []):
        if text.startswith(f"🏪 {s['name']}"):
            sess["report"]["shop_name"], sess["report"]["shop_id"] = s["name"], s["id"]
            sess.pop("nearby_shops", None); sess["step"] = "photo"
            return bot.send_message(uid, f"✅ {s['name']}\n\n📸 <b>2-qadam: Foto</b>", parse_mode="HTML", reply_markup=back_kb())
    bot.send_message(uid, "⚠️ Ro'yxatdan tanlang.")

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "new_shop")
def new_shop_name(msg):
    uid, sess, text = msg.from_user.id, sessions[uid], msg.text.strip()
    if text == "⬅️ Orqaga":
        nearby = find_nearby_shops(sess["report"]["location"]["lat"], sess["report"]["location"]["lon"], 100)
        if nearby:
            sess["step"], sess["nearby_shops"] = "shop_select", nearby
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for s in nearby: kb.add(f"🏪 {s['name']} ({s['distance']}m)")
            kb.add("🆕 Yangi magazin", "⬅️ Orqaga")
            return bot.send_message(uid, "📡 100m ichidagi magazinlar:", reply_markup=kb)
        return bot.send_message(uid, "🏪 Yangi magazin nomini yozing:", reply_markup=back_kb())
    if len(text) < 2: return bot.send_message(uid, "⚠️ Kamida 2 belgi.")
    lat, lon = sess["report"]["location"]["lat"], sess["report"]["location"]["lon"]
    shop = add_shop(text, lat, lon)
    sess["report"]["shop_name"], sess["report"]["shop_id"] = shop["name"], shop["id"]
    sess["step"] = "photo"
    bot.send_message(uid, f"✅ Yangi magazin: <b>{shop['name']}</b>\n\n📸 <b>2-qadam: Foto</b>", parse_mode="HTML", reply_markup=back_kb())

@bot.message_handler(content_types=["photo"])
def receive_photo(msg):
    uid = msg.from_user.id; sess = sessions.get(uid)
    if not sess or sess["step"] != "photo": return
    if msg.forward_date or msg.media_group_id: return bot.send_message(uid, "❌ Faqat kameradan jonli foto!")
    if int(time.time()) - msg.date > 120: return bot.send_message(uid, "❌ Eski foto!")
    sess["report"]["photo_id"], sess["report"]["photo_time"] = msg.photo[-1].file_id, now_str()
    sess["step"], sess["report"]["product_counts"] = "products", {}
    pl = "\n".join(f"  {i+1}. {p['name']} — {fmt(p['price'])} so'm" for i, p in enumerate(PRODUCTS))
    bot.send_message(uid, f"✅ Foto qabul qilindi!\n\n📦 <b>3-qadam: Mahsulotlar</b>\n\n{pl}", parse_mode="HTML", reply_markup=products_kb({}))

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "products")
def select_product(msg):
    uid, sess, text = msg.from_user.id, sessions[uid], msg.text
    if text == "✅ Tayyor":
        if not sess["report"]["product_counts"]: return bot.send_message(uid, "⚠️ Kamida 1 ta mahsulot!")
        sess["step"], sess["report"]["vozvrat_counts"] = "vozvrat", {}
        return bot.send_message(uid, "🔄 <b>4-qadam: Vozvratlar</b>\n\nQaytarilgan mahsulotlar. Yo'q bo'lsa ✅ Tayyor:", parse_mode="HTML", reply_markup=products_kb({}))
    for i, p in enumerate(PRODUCTS):
        cnt = sess["report"]["product_counts"].get(str(i), 0)
        if text in (p['name'], f"{p['name']} [{cnt} ta]"):
            sess["step"], sess["selected_product"], sess["qty_input"] = "qty_sale", i, ""
            return bot.send_message(uid, f"📦 <b>{p['name']}</b>\nNarxi: {fmt(p['price'])} so'm\n\nSoni: <b>0</b>", parse_mode="HTML", reply_markup=qty_numpad_kb())

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "qty_sale")
def receive_qty_sale(msg):
    uid, sess, text = msg.from_user.id, sessions[uid], msg.text.strip()
    idx, p = sess["selected_product"], PRODUCTS[sess["selected_product"]]
    nm = {"1️⃣":"1","2️⃣":"2","3️⃣":"3","4️⃣":"4","5️⃣":"5","6️⃣":"6","7️⃣":"7","8️⃣":"8","9️⃣":"9","0️⃣":"0"}
    if text in nm:
        cur = sess.get("qty_input","") + nm[text]; cur = "0" if cur.lstrip("0")=="" else str(int(cur))
        sess["qty_input"] = cur; qty = int(cur)
        bot.send_message(uid, f"📦 <b>{p['name']}</b>\nSoni: <b>{cur}</b> ta" + (f"\nJami: <b>{fmt(qty*p['price'])} so'm</b>" if qty>0 else ""), parse_mode="HTML", reply_markup=qty_numpad_kb())
    elif text == "🔙":
        cur = sess.get("qty_input",""); cur = cur[:-1] if len(cur)>1 else "0"; sess["qty_input"] = cur
        bot.send_message(uid, f"📦 <b>{p['name']}</b>\nSoni: <b>{cur}</b> ta", parse_mode="HTML", reply_markup=qty_numpad_kb())
    elif text == "✅ Tasdiqlash":
        qty = int(sess.get("qty_input","0")); sess.pop("qty_input",None)
        if qty>0: sess["report"]["product_counts"][str(idx)] = qty
        else: sess["report"]["product_counts"].pop(str(idx), None)
        sess["step"] = "products"
        bot.send_message(uid, f"✅ <b>{p['name']}</b> — {qty} ta" + (f" ({fmt(qty*p['price'])} so'm)" if qty>0 else ""), parse_mode="HTML", reply_markup=products_kb(sess["report"]["product_counts"]))
    elif text == "⬅️ Orqaga": sess.pop("qty_input",None); sess["step"]="products"; bot.send_message(uid, "↩️", reply_markup=products_kb(sess["report"]["product_counts"]))
    else: bot.send_message(uid, "⚠️ Tugmalardan foydalaning!")

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "vozvrat")
def select_vozvrat(msg):
    uid, sess, text = msg.from_user.id, sessions[uid], msg.text
    if text == "✅ Tayyor": sess["report"]["expired"]=[]; return finish_report(uid)
    for i, p in enumerate(PRODUCTS):
        cnt = sess["report"]["vozvrat_counts"].get(str(i),0)
        if text in (p['name'], f"{p['name']} [{cnt} ta]"):
            sess["step"], sess["selected_product"], sess["qty_input"] = "qty_vozvrat", i, ""
            return bot.send_message(uid, f"🔄 <b>{p['name']}</b>\n\nSoni: <b>0</b>", parse_mode="HTML", reply_markup=qty_numpad_kb())

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id, {}).get("step") == "qty_vozvrat")
def receive_qty_vozvrat(msg):
    uid, sess, text = msg.from_user.id, sessions[uid], msg.text.strip()
    idx, p = sess["selected_product"], PRODUCTS[sess["selected_product"]]
    nm = {"1️⃣":"1","2️⃣":"2","3️⃣":"3","4️⃣":"4","5️⃣":"5","6️⃣":"6","7️⃣":"7","8️⃣":"8","9️⃣":"9","0️⃣":"0"}
    if text in nm:
        cur = sess.get("qty_input","")+nm[text]; cur = "0" if cur.lstrip("0")=="" else str(int(cur))
        sess["qty_input"] = cur; bot.send_message(uid, f"🔄 <b>{p['name']}</b>\nSoni: <b>{cur}</b> ta", parse_mode="HTML", reply_markup=qty_numpad_kb())
    elif text == "🔙":
        cur = sess.get("qty_input",""); cur = cur[:-1] if len(cur)>1 else "0"; sess["qty_input"]=cur
        bot.send_message(uid, f"🔄 <b>{p['name']}</b>\nSoni: <b>{cur}</b> ta", parse_mode="HTML", reply_markup=qty_numpad_kb())
    elif text == "✅ Tasdiqlash":
        qty = int(sess.get("qty_input","0")); sess.pop("qty_input",None)
        if qty>0: sess["report"]["vozvrat_counts"][str(idx)] = qty
        else: sess["report"]["vozvrat_counts"].pop(str(idx), None)
        sess["step"]="vozvrat"; bot.send_message(uid, f"✅ <b>{p['name']}</b> vozvrat — {qty} ta", parse_mode="HTML", reply_markup=products_kb(sess["report"]["vozvrat_counts"]))
    elif text == "⬅️ Orqaga": sess.pop("qty_input",None); sess["step"]="vozvrat"; bot.send_message(uid, "↩️", reply_markup=products_kb(sess["report"]["vozvrat_counts"]))
    else: bot.send_message(uid, "⚠️ Tugmalardan foydalaning!")

def finish_report(uid):
    sess = sessions.get(uid); r = sess["report"]; r["finished"] = now_str()
    sl, ts = [], 0
    for i, q in r.get("product_counts",{}).items(): s=q*PRODUCTS[int(i)]["price"]; ts+=s; sl.append(f"  • {PRODUCTS[int(i)]['name']}: {q} ta = {fmt(s)} so'm")
    vl, tv = [], 0
    for i, q in r.get("vozvrat_counts",{}).items(): s=q*PRODUCTS[int(i)]["price"]; tv+=s; vl.append(f"  • {PRODUCTS[int(i)]['name']}: {q} ta = {fmt(s)} so'm")
    nt = ts-tv; r["total_sale"], r["total_vozv"], r["net_total"] = ts, tv, nt
    d=load(); d["reports"].append(r)
    if str(uid) in d["users"]: d["users"][str(uid)]["total_visits"] = d["users"][str(uid)].get("total_visits",0)+1
    save(d)
    st="\n".join(sl) or "  —"; vt="\n".join(vl) or "  —"
    sm = f"━━━━━━━━━━━━━━━━━━━━\n✅ <b>Hisobot yakunlandi!</b>\n━━━━━━━━━━━━━━━━━━━━\n🏪 {r.get('shop_name','')}\n🕐 {r['started']} → {r['finished']}\n\n📦 Sotuv:\n{st}\n💰 Sotuv jami: <b>{fmt(ts)} so'm</b>\n\n🔄 Vozvrat:\n{vt}\n↩️ Vozvrat jami: <b>{fmt(tv)} so'm</b>\n\n💵 Sof: <b>{fmt(nt)} so'm</b>\n━━━━━━━━━━━━━━━━━━━━"
    bot.send_message(uid, sm, parse_mode="HTML", reply_markup=main_kb(get_user(uid)["role"]))
    at = f"━━━━━━━━━━━━━━━━━━━━\n📋 <b>Yangi hisobot</b>\n━━━━━━━━━━━━━━━━━━━━\n👤 {r['agent_name']}\n🏪 {r.get('shop_name','')}\n🕐 {r['started']} → {r['finished']}\n\n📦 Sotuv:\n{st}\n💰 Sotuv: <b>{fmt(ts)} so'm</b>\n\n🔄 Vozvrat:\n{vt}\n↩️ Vozvrat: <b>{fmt(tv)} so'm</b>\n\n💵 Sof: <b>{fmt(nt)} so'm</b>\n━━━━━━━━━━━━━━━━━━━━"
    bot.send_photo(ADMIN_ID, r["photo_id"], caption=at, parse_mode="HTML")
    bot.send_location(ADMIN_ID, r["location"]["lat"], r["location"]["lon"])
    d2=load()
    for u_id,u in d2["users"].items():
        if u.get("role") in ("supervisor","manager") and u.get("approved"):
            try: bot.send_message(int(u_id), f"📋 Yangi hisobot!\n👤 {r['agent_name']}\n🏪 {r.get('shop_name','')}\n💰 Sotuv: {fmt(ts)} so'm | Sof: {fmt(nt)} so'm", parse_mode="HTML")
            except: pass
    sessions.pop(uid, None)

# =============================================
# 📊 HISOBOT TIZIMI (qisqartirilgan)
# =============================================
def get_reports_by_period(sd, ed, aid=None, pi=None, sn=None):
    res=[]
    for r in load()["reports"]:
        rd=r.get("date",r.get("started","")[:10])
        if sd<=rd<=ed:
            if aid and str(r.get("agent_id"))!=str(aid): continue
            if pi is not None and int(r.get("product_counts",{}).get(str(pi),0))==0: continue
            if sn and r.get("shop_name","").lower()!=sn.lower(): continue
            res.append(r)
    return res

def calc_stats(reps):
    if not reps: return None
    ts=tv=0; ag={}; pr={i:{"name":p["name"],"price":p["price"],"qty":0,"sum":0} for i,p in enumerate(PRODUCTS)}
    vz={i:{"name":p["name"],"qty":0,"sum":0} for i,p in enumerate(PRODUCTS)}; sh={}
    for r in reps:
        ts+=r.get("total_sale",0); tv+=r.get("total_vozv",0)
        an=r.get("agent_name","?"); ag[an]=ag.get(an,{"visits":0,"sale":0,"vozv":0,"net":0}); ag[an]["visits"]+=1; ag[an]["sale"]+=r.get("total_sale",0); ag[an]["vozv"]+=r.get("total_vozv",0); ag[an]["net"]+=r.get("net_total",0)
        for i,q in r.get("product_counts",{}).items(): ii=int(i); pr[ii]["qty"]+=q; pr[ii]["sum"]+=q*pr[ii]["price"]
        for i,q in r.get("vozvrat_counts",{}).items(): ii=int(i); vz[ii]["qty"]+=q; vz[ii]["sum"]+=q*PRODUCTS[ii]["price"]
        sn=r.get("shop_name","?"); sh[sn]=sh.get(sn,{"visits":0,"sale":0,"vozv":0,"net":0}); sh[sn]["visits"]+=1; sh[sn]["sale"]+=r.get("total_sale",0); sh[sn]["vozv"]+=r.get("total_vozv",0); sh[sn]["net"]+=r.get("net_total",0)
    return {"total_visits":len(reps),"total_agents":len(ag),"total_sale":ts,"total_vozv":tv,"net_total":ts-tv,"agents":ag,"products":pr,"vozvrat":vz,"shops":sh,"reps":reps}

def fmt_report(stats, title=""):
    if not stats: return f"📭 {title}: ma'lumot yo'q."
    t=f"━━━━━━━━━━━━━━━━━━━━\n📊 <b>{title}</b>\n━━━━━━━━━━━━━━━━━━━━\n👥 Agentlar: <b>{stats['total_agents']}</b>\n🏪 Visit: <b>{stats['total_visits']}</b>\n🏬 Magazin: <b>{len(stats['shops'])}</b>\n\n📦 <b>Mahsulotlar:</b>\n"
    for p in stats["products"].values():
        if p["qty"]>0: t+=f"  • {p['name']}: {p['qty']} ta — {fmt(p['sum'])} so'm\n"
    if all(p["qty"]==0 for p in stats["products"].values()): t+="  —\n"
    if any(v["qty"]>0 for v in stats["vozvrat"].values()):
        t+="\n🔄 <b>Vozvrat:</b>\n"
        for v in stats["vozvrat"].values():
            if v["qty"]>0: t+=f"  • {v['name']}: {v['qty']} ta — {fmt(v['sum'])} so'm\n"
    t+=f"\n💰 Sotuv: <b>{fmt(stats['total_sale'])} so'm</b>\n↩️ Vozvrat: <b>{fmt(stats['total_vozv'])} so'm</b>\n💵 Sof: <b>{fmt(stats['net_total'])} so'm</b>\n━━━━━━━━━━━━━━━━━━━━"
    if stats["agents"]:
        sa=sorted(stats["agents"].items(),key=lambda x:x[1]["net"],reverse=True)
        t+="\n\n👤 <b>TOP Agentlar:</b>\n"
        for i,(n,a) in enumerate(sa[:10]): t+=f"  {i+1}. {n} — {a['visits']} Visit, {fmt(a['net'])} so'm\n"
    if stats["shops"]:
        ss=sorted(stats["shops"].items(),key=lambda x:x[1]["net"],reverse=True)
        t+="\n🏪 <b>TOP Magazinlar:</b>\n"
        for i,(n,s) in enumerate(ss[:10]): t+=f"  {i+1}. {n} — {s['visits']} Visit, {fmt(s['net'])} so'm\n"
    return t

def gen_excel(reps, fn="hisobot.csv"):
    p="/tmp/"+fn
    with open(p,"w",encoding="utf-8-sig") as f:
        h="Sana,Agent,Magazin"
        for pr in PRODUCTS: h+=f",{pr['name']} (dona),{pr['name']} (so'm)"
        h+=",Sotuv jami,Vozvrat jami,Sof daromad\n"; f.write(h)
        for r in reps:
            l=f"{r.get('date','')},{r.get('agent_name','')},{r.get('shop_name','')}"
            for i,pr in enumerate(PRODUCTS): q=r.get("product_counts",{}).get(str(i),0); l+=f",{q},{q*pr['price']}"
            l+=f",{r.get('total_sale',0)},{r.get('total_vozv',0)},{r.get('net_total',0)}\n"; f.write(l)
    return p

def send_report_menu(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📅 Bugun","📆 Bu oy"); kb.add("👤 Agent bo'yicha","📦 Mahsulot bo'yicha"); kb.add("🏪 Magazin bo'yicha","🗓 Sana oralig'i"); kb.add("📤 Excel yuklash","📋 Batafsil hisobot"); kb.add("⬅️ Orqaga")
    bot.send_message(uid, "📊 <b>Hisobotlar paneli</b>", parse_mode="HTML", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📊 Mening hisobotlarim")
def my_reports(msg):
    uid=msg.from_user.id
    if get_user(uid).get("role")!="agent": return
    sessions[uid]={"step":"my_report_menu","agent_filter":uid}; send_report_menu(uid)

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id,{}).get("step")=="my_report_menu")
def my_rep(msg):
    uid,us=msg.from_user.id,get_user(msg.from_user.id); tx=msg.text; ai=sessions[uid].get("agent_filter",uid)
    if tx=="⬅️ Orqaga": sessions.pop(uid,None); return bot.send_message(uid,"↩️",reply_markup=main_kb(us["role"]))
    if tx=="📅 Bugun": reps=get_reports_by_period(today_str(),today_str(),ai); bot.send_message(uid,fmt_report(calc_stats(reps),"Bugun"),parse_mode="HTML")
    elif tx=="📆 Bu oy": reps=get_reports_by_period(datetime.now().strftime("%Y-%m-01"),today_str(),ai); bot.send_message(uid,fmt_report(calc_stats(reps),"Bu oy"),parse_mode="HTML")
    elif tx=="📤 Excel yuklash": reps=get_reports_by_period("2000-01-01",today_str(),ai); p=gen_excel(reps); bot.send_document(uid,open(p,"rb"),caption="📤 Hisobot (Excel)")
    elif tx=="📦 Mahsulot bo'yicha": show_product_filter(uid,"my_report_menu")
    elif tx=="🏪 Magazin bo'yicha": show_shop_filter(uid,"my_report_menu")
    elif tx=="📋 Batafsil hisobot": reps=get_reports_by_period("2000-01-01",today_str(),ai); bot.send_message(uid,fmt_report(calc_stats(reps),"Barcha hisobotlarim"),parse_mode="HTML")
    elif tx=="🗓 Sana oralig'i": sessions[uid]["step"]="my_date_from"; bot.send_message(uid,"Boshlanish sanasi:\n<i>2026-04-01</i>",parse_mode="HTML",reply_markup=back_kb())

def is_mgr(uid): return is_admin(uid) or get_user(uid).get("role") in ("supervisor","manager")

@bot.message_handler(func=lambda m: m.text=="📊 Hisobotlar" and is_mgr(m.from_user.id))
def admin_reports(msg):
    uid=msg.from_user.id; sessions[uid]={"step":"admin_report_menu","agent_filter":None}; send_report_menu(uid)

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id,{}).get("step")=="admin_report_menu")
def adm_rep(msg):
    uid=msg.from_user.id; us=get_user(uid); tx=msg.text; ai=sessions[uid].get("agent_filter")
    rl="admin" if is_admin(uid) else us["role"]
    if tx=="⬅️ Orqaga": sessions.pop(uid,None); return bot.send_message(uid,"↩️",reply_markup=admin_kb() if is_admin(uid) else main_kb(rl))
    if tx=="📅 Bugun": reps=get_reports_by_period(today_str(),today_str(),ai); bot.send_message(uid,fmt_report(calc_stats(reps),"Bugun"),parse_mode="HTML")
    elif tx=="📆 Bu oy": reps=get_reports_by_period(datetime.now().strftime("%Y-%m-01"),today_str(),ai); bot.send_message(uid,fmt_report(calc_stats(reps),"Bu oy"),parse_mode="HTML")
    elif tx=="📤 Excel yuklash": reps=get_reports_by_period("2000-01-01",today_str(),ai); p=gen_excel(reps); bot.send_document(uid,open(p,"rb"),caption="📤 Hisobot (Excel)")
    elif tx=="👤 Agent bo'yicha": show_agent_filter(uid,"admin_report_menu")
    elif tx=="📦 Mahsulot bo'yicha": show_product_filter(uid,"admin_report_menu")
    elif tx=="🏪 Magazin bo'yicha": show_shop_filter(uid,"admin_report_menu")
    elif tx=="📋 Batafsil hisobot": reps=get_reports_by_period("2000-01-01",today_str(),ai); bot.send_message(uid,fmt_report(calc_stats(reps),"Barcha"),parse_mode="HTML")
    elif tx=="🗓 Sana oralig'i": sessions[uid]["step"]="admin_date_from"; bot.send_message(uid,"Boshlanish sanasi:\n<i>2026-04-01</i>",parse_mode="HTML",reply_markup=back_kb())

def show_agent_filter(uid,rs):
    agents=[(u_id,u) for u_id,u in load()["users"].items() if u.get("role")=="agent"]
    if not agents: return bot.send_message(uid,"Hali agent yo'q.")
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True); kb.add("🌐 Barcha agentlar")
    for u_id,u in agents: kb.add(f"{u['name']} [{u_id}]")
    kb.add("⬅️ Orqaga"); sessions[uid]={"step":"pick_agent","agent_return":rs,"agents_map":{f"{u['name']} [{u_id}]":u_id for u_id,u in agents}}
    bot.send_message(uid,"👤 Agentni tanlang:",reply_markup=kb)

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id,{}).get("step")=="pick_agent")
def pick_agent(msg):
    uid,tx=msg.from_user.id,msg.text; rs=sessions[uid].get("agent_return","admin_report_menu")
    if tx=="⬅️ Orqaga": sessions[uid]={"step":rs,"agent_filter":None}; return send_report_menu(uid)
    if tx=="🌐 Barcha agentlar": sessions[uid]["agent_filter"]=None
    else:
        am=sessions[uid].get("agents_map",{})
        if tx in am: sessions[uid]["agent_filter"]=am[tx]
        else: return bot.send_message(uid,"⚠️ Agentni tanlang.")
    sessions[uid]["step"]=rs
    bot.send_message(uid,f"✅ Agent: <b>{tx}</b>",parse_mode="HTML"); send_report_menu(uid)

def show_product_filter(uid,rs):
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True); kb.add("📦 Barcha mahsulotlar")
    for p in PRODUCTS: kb.add(p['name'])
    kb.add("⬅️ Orqaga"); sessions[uid]={"step":"pick_product","product_return":rs}
    bot.send_message(uid,"📦 Mahsulotni tanlang:",reply_markup=kb)

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id,{}).get("step")=="pick_product")
def pick_product(msg):
    uid,tx=msg.from_user.id,msg.text; rs=sessions[uid].get("product_return","admin_report_menu")
    if tx=="⬅️ Orqaga": sessions[uid]={"step":rs,"agent_filter":sessions[uid].get("agent_filter")}; return send_report_menu(uid)
    pi=None
    if tx!="📦 Barcha mahsulotlar":
        for i,p in enumerate(PRODUCTS):
            if tx==p['name']: pi=i; break
        if pi is None: return bot.send_message(uid,"⚠️ Mahsulotni tanlang.")
    ai=sessions[uid].get("agent_filter"); reps=get_reports_by_period("2000-01-01",today_str(),ai,pi)
    bot.send_message(uid,fmt_report(calc_stats(reps),f"Mahsulot: {tx}"),parse_mode="HTML")
    sessions[uid]={"step":rs,"agent_filter":ai}; send_report_menu(uid)

def show_shop_filter(uid,rs):
    sn=set()
    for r in load()["reports"]:
        if r.get("shop_name"): sn.add(r["shop_name"])
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True); kb.add("🏬 Barcha magazinlar")
    for n in sorted(sn): kb.add(f"🏪 {n}")
    kb.add("⬅️ Orqaga"); sessions[uid]={"step":"pick_shop","shop_return":rs}
    bot.send_message(uid,"🏪 Magazinni tanlang:",reply_markup=kb)

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id,{}).get("step")=="pick_shop")
def pick_shop(msg):
    uid,tx=msg.from_user.id,msg.text; rs=sessions[uid].get("shop_return","admin_report_menu")
    if tx=="⬅️ Orqaga": sessions[uid]={"step":rs,"agent_filter":sessions[uid].get("agent_filter")}; return send_report_menu(uid)
    sn=None
    if tx!="🏬 Barcha magazinlar": sn=tx.replace("🏪 ","")
    ai=sessions[uid].get("agent_filter"); reps=get_reports_by_period("2000-01-01",today_str(),ai,sn=sn)
    bot.send_message(uid,fmt_report(calc_stats(reps),f"Magazin: {sn or 'Barcha'}"),parse_mode="HTML")
    sessions[uid]={"step":rs,"agent_filter":ai}; send_report_menu(uid)

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id,{}).get("step") in ("my_date_from","admin_date_from"))
def date_from(msg):
    uid,ss=msg.from_user.id,sessions[uid]; tx=msg.text.strip()
    if tx=="⬅️ Orqaga": rs="my_report_menu" if ss["step"]=="my_date_from" else "admin_report_menu"; sessions[uid]={"step":rs,"agent_filter":ss.get("agent_filter")}; return send_report_menu(uid)
    try:
        datetime.strptime(tx,"%Y-%m-%d"); ss["date_from"]=tx
        ss["step"]="my_date_to" if "my" in ss["step"] else "admin_date_to"
        bot.send_message(uid,"Tugash sanasi:\n<i>2026-04-30</i>",parse_mode="HTML")
    except: bot.send_message(uid,"❌ Format: 2026-04-01")

@bot.message_handler(func=lambda m: sessions.get(m.from_user.id,{}).get("step") in ("my_date_to","admin_date_to"))
def date_to(msg):
    uid,ss=msg.from_user.id,sessions[uid]; tx=msg.text.strip()
    if tx=="⬅️ Orqaga": rs="my_report_menu" if ss["step"]=="my_date_to" else "admin_report_menu"; sessions[uid]={"step":rs,"agent_filter":ss.get("agent_filter")}; return send_report_menu(uid)
    try:
        datetime.strptime(tx,"%Y-%m-%d"); rs="my_report_menu" if ss["step"]=="my_date_to" else "admin_report_menu"
        df,dt=ss["date_from"],tx; sessions[uid]["step"]=rs
        reps=get_reports_by_period(df,dt,ss.get("agent_filter"))
        bot.send_message(uid,fmt_report(calc_stats(reps),f"{df} → {dt}"),parse_mode="HTML")
        send_report_menu(uid)
    except: bot.send_message(uid,"❌ Format: 2026-04-30")

# =============================================
# QOLGAN BO'LIMLAR
# =============================================
@bot.message_handler(func=lambda m: m.text=="👥 Foydalanuvchilar" and is_admin(m.from_user.id))
def admin_users(msg):
    d=load(); t="👥 <b>Foydalanuvchilar:</b>\n\n"
    for uid,u in d["users"].items():
        if str(uid)==str(ADMIN_ID): continue
        t+=f"{ROLES.get(u['role'],'')} <b>{u['name']}</b>\n   🆔 {uid} | 🏪 {u.get('total_visits',0)} Visit\n\n"
    bot.send_message(ADMIN_ID,t,parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text=="👥 Agentlar" and is_mgr(m.from_user.id))
def view_agents(msg):
    uid=msg.from_user.id; d=load()
    agents=[(u_id,u) for u_id,u in d["users"].items() if u.get("role")=="agent" and u.get("approved")]
    if not agents: return bot.send_message(uid,"Hali agent yo'q.")
    t="👥 <b>Agentlar:</b>\n\n"
    for u_id,u in agents:
        reps=[r for r in d["reports"] if str(r.get("agent_id"))==u_id]
        td=[r for r in reps if r.get("date")==today_str()]
        t+=f"👤 <b>{u['name']}</b>\n   🏪 Jami: {len(reps)} | 📅 Bugun: {len(td)}\n\n"
    bot.send_message(uid,t,parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text=="🏆 Reyting" and is_mgr(m.from_user.id))
def rating(msg):
    uid=msg.from_user.id; d=load(); sc=[]
    for u_id,u in d["users"].items():
        if u.get("role")!="agent": continue
        reps=[r for r in d["reports"] if str(r.get("agent_id"))==u_id]
        sc.append((u["name"],len(reps),sum(r.get("net_total",0) for r in reps)))
    sc.sort(key=lambda x:x[2],reverse=True)
    md=["🥇","🥈","🥉"]; t="🏆 <b>Reyting</b>\n\n"
    for i,(n,v,tot) in enumerate(sc): ic=md[i] if i<3 else f"{i+1}."; t+=f"{ic} <b>{n}</b>\n   🏪 {v} Visit | 💵 {fmt(tot)} so'm\n\n"
    bot.send_message(uid,t or "Ma'lumot yo'q.",parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text=="💰 Sotuv statistikasi" and is_mgr(m.from_user.id))
def sales_stats(msg):
    uid=msg.from_user.id; rt=get_reports_by_period(today_str(),today_str()); rm=get_reports_by_period(datetime.now().strftime("%Y-%m-01"),today_str())
    stt=calc_stats(rt); stm=calc_stats(rm); t="💰 <b>Sotuv statistikasi</b>\n━━━━━━━━━━━━━━━━━━━━\n📅 <b>Bugun:</b>\n"
    if stt and stt["total_visits"]>0:
        t+=f"  Visit: {stt['total_visits']}\n"
        for p in stt["products"].values():
            if p["qty"]>0: t+=f"  • {p['name']}: {p['qty']} ta = {fmt(p['sum'])} so'm\n"
        t+=f"  💵 Sof: <b>{fmt(stt['net_total'])} so'm</b>\n"
    else: t+="  —\n"
    t+="\n📆 <b>Bu oy:</b>\n"
    if stm and stm["total_visits"]>0:
        t+=f"  Visit: {stm['total_visits']}\n"
        for p in stm["products"].values():
            if p["qty"]>0: t+=f"  • {p['name']}: {p['qty']} ta = {fmt(p['sum'])} so'm\n"
        t+=f"  💵 Sof: <b>{fmt(stm['net_total'])} so'm</b>\n"
    else: t+="  —\n"
    t+="━━━━━━━━━━━━━━━━━━━━"
    bot.send_message(uid,t,parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text=="🏪 Magazinlar" and is_mgr(m.from_user.id))
def list_shops(msg):
    uid=msg.from_user.id; sh=load_shops()
    if not sh: return bot.send_message(uid,"🏪 Magazin yo'q.")
    t="🏪 <b>Magazinlar:</b>\n\n"
    for s in sh: t+=f"  🆔 {s['id']}. <b>{s['name']}</b>\n     📍 {s['lat']}, {s['lon']}\n\n"
    bot.send_message(uid,t,parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text=="⏳ Kutayotganlar" and is_admin(m.from_user.id))
def pending_list(msg):
    d=load()
    if not d.get("pending"): return bot.send_message(ADMIN_ID,"⏳ Kutayotgan so'rov yo'q.")
    for u_id,p in d["pending"].items():
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅",callback_data=f"approve_{u_id}_{p['role']}"),types.InlineKeyboardButton("❌",callback_data=f"reject_{u_id}"))
        bot.send_message(ADMIN_ID,f"⏳ {p['name']}\n🆔 {u_id}\n🎭 {ROLES.get(p['role'],'')}",parse_mode="HTML",reply_markup=kb)

print("✅ Bot ishga tushdi...")
bot.infinity_polling()