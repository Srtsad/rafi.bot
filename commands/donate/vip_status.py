import json
import os
from datetime import datetime, timedelta
from aiogram import Router, types

status_router = Router()

DB_PLAYERS = "database/players.json"
DB_DONATE = "database-donate/donate.json"
DB_ADMINS = "database/status/admins.json"

OWNER_ID = 852666681
STATUS_DURATION = timedelta(days=15)

# =========================
# SAFE SEND
# =========================
async def safe(msg, text):
    try:
        await msg.answer(text)
    except:
        pass

# =========================
# Статусы
# =========================
VIP_STATUSES = {
    "standart": {"name": "Standart", "price": 75, "emoji": "✨"},
    "gold": {"name": "Gold", "price": 150, "emoji": "🟡"},
    "platinum": {"name": "Platinum", "price": 270, "emoji": "🔷"},
    "legendary": {"name": "Legendary", "price": 500, "emoji": "👑"},
    "admins": {"name": "Admins", "price": 0, "emoji": "🛡️"}
}

# =========================
# JSON helpers
# =========================
def load_json(path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =========================
# Проверка админа
# =========================
def is_admin(user_id: int):
    if user_id == OWNER_ID:
        return True
    if not os.path.exists(DB_ADMINS):
        return False
    admins = load_json(DB_ADMINS)
    return str(user_id) in admins

# =========================
# Игрок
# =========================
def get_player(user_id: int):
    players = load_json(DB_PLAYERS)
    if str(user_id) not in players:
        players[str(user_id)] = {
            "user_id": user_id,
            "username": f"Игрок {user_id}",
            "tg_username": "",
            "status": None,
            "status_end": None
        }
        save_json(DB_PLAYERS, players)
    return players[str(user_id)]

def save_player(user_id: int, data: dict):
    players = load_json(DB_PLAYERS)
    players[str(user_id)] = data
    save_json(DB_PLAYERS, players)

# =========================
# RAF
# =========================
def get_raf(user_id: int):
    donate = load_json(DB_DONATE)
    if str(user_id) not in donate:
        donate[str(user_id)] = {"raf-coin": 0}
        save_json(DB_DONATE, donate)
    return donate[str(user_id)]

def save_raf(user_id: int, data: dict):
    donate = load_json(DB_DONATE)
    donate[str(user_id)] = data
    save_json(DB_DONATE, donate)

# =========================
# Поиск игрока
# =========================
def find_user_by_username(username: str):
    players = load_json(DB_PLAYERS)
    for uid, pdata in players.items():
        if pdata.get("username","").lower() == username.lower() or \
           (pdata.get("tg_username") or "").lower() == f"@{username.lower()}":
            return int(uid), pdata
    return None, None

# =========================
# Формат времени
# =========================
def format_time(iso):
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return "—"

# =====================================================
# Купить статус
# =====================================================
@status_router.message(lambda m: m.text and m.text.lower().startswith("купить статус"))
async def buy_status(message: types.Message):
    parts = message.text.split()

    if len(parts) < 3:
        txt = "💎 Доступные статусы:\n\n"
        for k, v in VIP_STATUSES.items():
            if k != "admins":
                txt += f"{v['emoji']} {v['name']} — {v['price']} Raf\n"
        txt += "\nПример: Купить статус Gold"
        return await safe(message, txt)

    status_name = parts[2].lower()

    if status_name not in VIP_STATUSES or status_name == "admins":
        return await safe(message,"❌ Такого статуса нет")

    user = message.from_user
    raf = get_raf(user.id)
    price = VIP_STATUSES[status_name]["price"]

    if raf["raf-coin"] < price:
        return await safe(message,f"❌ Нужно {price} Raf")

    raf["raf-coin"] -= price
    save_raf(user.id, raf)

    player = get_player(user.id)
    player["status"] = VIP_STATUSES[status_name]["name"]
    player["status_end"] = (datetime.utcnow() + STATUS_DURATION).isoformat()
    save_player(user.id, player)

    await safe(
        message,
        f"✅ Куплен статус {VIP_STATUSES[status_name]['emoji']} {VIP_STATUSES[status_name]['name']}\n"
        f"⏳ До: {format_time(player['status_end'])}\n"
        f"🪙 Осталось Raf: {raf['raf-coin']}"
    )

# =====================================================
# Выдать статус
# =====================================================
@status_router.message(lambda m: m.text and m.text.lower().startswith("выдать статус"))
async def give_status(message: types.Message):
    if not is_admin(message.from_user.id):
        return await safe(message,"❌ Нет прав")

    args = message.text.split()
    if len(args) < 4:
        return await safe(message,"Пример: Выдать статус @user Gold")

    username = args[2].replace("@","")
    status_name = args[3].lower()

    if status_name not in VIP_STATUSES:
        return await safe(message,"❌ Нет такого статуса")

    target_id, target = find_user_by_username(username)
    if not target:
        return await safe(message,"❌ Игрок не найден")

    target["status"] = VIP_STATUSES[status_name]["name"]
    target["status_end"] = (datetime.utcnow() + STATUS_DURATION).isoformat()
    save_player(target_id, target)

    await safe(message,f"✅ Выдан {VIP_STATUSES[status_name]['name']}")

# =====================================================
# Забрать статус
# =====================================================
@status_router.message(lambda m: m.text and m.text.lower().startswith("забрать статус"))
async def remove_status(message: types.Message):
    if not is_admin(message.from_user.id):
        return await safe(message,"❌ Нет прав")

    args = message.text.split()
    if len(args) < 3:
        return await safe(message,"Пример: Забрать статус @user")

    username = args[2].replace("@","")
    target_id, target = find_user_by_username(username)

    if not target:
        return await safe(message,"❌ Игрок не найден")

    target["status"] = None
    target["status_end"] = None
    save_player(target_id, target)

    await safe(message,"❌ Статус снят")

# =====================================================
# Мой статус
# =====================================================
@status_router.message(lambda m: m.text and m.text.lower() == "мой статус")
async def my_status(message: types.Message):
    player = get_player(message.from_user.id)
    status = player.get("status") or "Новичок"
    end = format_time(player.get("status_end"))
    await safe(message,f"🏆 Статус: {status}\n⏳ До: {end}")
