"""
Savdo boti - Yaqin klientlar moduli
=====================================
Bu faylni mavjud botingizga import qiling.

Foydalanish:
1. Bu faylni bot.py bilan bir papkaga qo'ying
2. bot.py da: from nearby_clients import register_location_handler
3. register_location_handler(dp) ni chaqiring

Kerakli kutubxonalar:
  pip install aiogram openpyxl
"""

import math
import json
import os
from typing import List, Dict

# ─── Masofani hisoblash (Haversine formula) ────────────────────────────
def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Ikki nuqta orasidagi masofani metrda qaytaradi."""
    R = 6_371_000  # Yer radiusi (metr)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─── Klientlar ro'yxatini yuklash ──────────────────────────────────────
def load_clients(excel_path: str = "gps_klient1.xlsx") -> List[Dict]:
    """
    Excel fayldan klientlarni yuklaydi.
    Agar clients_cache.json mavjud bo'lsa, undan o'qiydi (tezroq).
    """
    cache_file = "clients_cache.json"

    # Cache mavjud bo'lsa o'qib olamiz
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # Excel dan o'qish
    try:
        import openpyxl
        wb = openpyxl.load_workbook(excel_path, read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))

        clients = []
        for row in rows[1:]:  # 1-qator - sarlavha
            if not row[0] or row[2] is None or row[3] is None:
                continue
            try:
                lat = float(row[2])
                lng = float(row[3])
                # Termiz mintaqasi koordinatalari tekshiruvi
                if not (36.0 < lat < 38.5 and 65.0 < lng < 68.5):
                    continue
                clients.append({
                    "name": str(row[0]).strip(),
                    "address": str(row[1]).strip() if row[1] else "—",
                    "lat": lat,
                    "lng": lng,
                })
            except (ValueError, TypeError):
                continue

        # Cache saqlaymiz
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(clients, f, ensure_ascii=False)

        return clients

    except ImportError:
        raise ImportError("openpyxl o'rnatilmagan: pip install openpyxl")
    except FileNotFoundError:
        raise FileNotFoundError(f"Excel fayl topilmadi: {excel_path}")


# ─── Yaqin klientlarni topish ─────────────────────────────────────────
def find_nearby(
    user_lat: float,
    user_lng: float,
    clients: List[Dict],
    radius_m: float = 100.0,
    max_results: int = 20,
) -> List[Dict]:
    """
    Foydalanuvchi koordinatasiga yaqin klientlarni qaytaradi.
    
    :param user_lat: Foydalanuvchi latitudasi
    :param user_lng: Foydalanuvchi longitudasi
    :param clients:  Barcha klientlar ro'yxati
    :param radius_m: Radius (metr), default 100m
    :param max_results: Maksimal natijalar soni
    :return: Masofasi bo'yicha tartiblangan yaqin klientlar
    """
    nearby = []
    for c in clients:
        dist = haversine_meters(user_lat, user_lng, c["lat"], c["lng"])
        if dist <= radius_m:
            nearby.append({**c, "distance_m": round(dist, 1)})

    nearby.sort(key=lambda x: x["distance_m"])
    return nearby[:max_results]


# ─── Aiogram handler ──────────────────────────────────────────────────
def register_location_handler(dp, excel_path: str = "gps_klient1.xlsx"):
    """
    Aiogram Dispatcher ga lokatsiya handlerini ro'yxatdan o'tkazadi.
    
    Foydalanish:
        from aiogram import Dispatcher
        from nearby_clients import register_location_handler
        
        dp = Dispatcher(bot)
        register_location_handler(dp)
    """
    from aiogram import types

    # Klientlarni bir marta yuklaymiz
    clients = load_clients(excel_path)
    print(f"✅ {len(clients)} ta klient yuklandi.")

    @dp.message_handler(content_types=types.ContentType.LOCATION)
    async def handle_location(message: types.Message):
        lat = message.location.latitude
        lng = message.location.longitude

        nearby = find_nearby(lat, lng, clients, radius_m=100)

        if not nearby:
            await message.reply(
                "📍 100 metr atrofida hech qanday klient topilmadi.\n"
                "Lokatsiyangizni tekshiring yoki radius kattaroq qilinsin."
            )
            return

        lines = [f"🏪 <b>100 metr ichidagi klientlar ({len(nearby)} ta):</b>\n"]
        for i, c in enumerate(nearby, 1):
            lines.append(
                f"{i}. <b>{c['name']}</b>\n"
                f"   📍 {c['address']}\n"
                f"   📏 {c['distance_m']} metr\n"
            )

        await message.reply("\n".join(lines), parse_mode="HTML")

    return handle_location


# ─── python-telegram-bot v20 uchun (alternativ) ───────────────────────
def get_ptb_location_handler(excel_path: str = "gps_klient1.xlsx"):
    """
    python-telegram-bot (v20+) uchun handler qaytaradi.
    
    Foydalanish:
        from telegram.ext import MessageHandler, filters, Application
        from nearby_clients import get_ptb_location_handler
        
        app = Application.builder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.LOCATION, get_ptb_location_handler()))
    """
    clients = load_clients(excel_path)
    print(f"✅ {len(clients)} ta klient yuklandi.")

    async def location_handler(update, context):
        loc = update.message.location
        nearby = find_nearby(loc.latitude, loc.longitude, clients, radius_m=100)

        if not nearby:
            await update.message.reply_text(
                "📍 100 metr atrofida hech qanday klient topilmadi."
            )
            return

        lines = [f"🏪 100 metr ichidagi klientlar ({len(nearby)} ta):\n"]
        for i, c in enumerate(nearby, 1):
            lines.append(
                f"{i}. {c['name']}\n"
                f"   📍 {c['address']}\n"
                f"   📏 {c['distance_m']} metr\n"
            )

        await update.message.reply_text("\n".join(lines))

    return location_handler


# ─── Test (to'g'ridan-to'g'ri ishlatish uchun) ────────────────────────
if __name__ == "__main__":
    clients = load_clients("gps_klient1.xlsx")
    print(f"Jami klientlar: {len(clients)}")

    # Test: Termiz port koordinatalari
    test_lat, test_lng = 37.2001, 67.2798
    result = find_nearby(test_lat, test_lng, clients, radius_m=100)

    print(f"\n100 metr ichida ({test_lat}, {test_lng}):")
    for c in result:
        print(f"  - {c['name']} | {c['distance_m']} m | {c['address']}")
