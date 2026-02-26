from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import json
import os
from datetime import datetime, timedelta

admin_router = Router()

ADMINS_FILE = "database/admins.json"
PROMO_FILE = "database/promocodes.json"
DB_PLAYERS = "database/players.json"
DB_DONATE = "database-donate/donate.json"
OWNER_ID = 852666681

# =========================
# SAFE SEND (чтобы бот не падал)
# =========================
async def safe_send(msg, text, **kwargs):
    try:
        await msg.answer(text, **kwargs)
    except:
        pass

# =========================
# Проверка админки
# =========================
def load_admins():
    if not os.path.exists(os.path.dirname(ADMINS_FILE)):
        os.makedirs(os.path.dirname(ADMINS_FILE), exist_ok=True)
    if not os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    with open(ADMINS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_admins(data):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def is_admin(user_id: int):
    if user_id == OWNER_ID:
        return True
    admins = load_admins()
    admins = [int(x) for x in admins]
    return int(user_id) in admins

# =========================
# OWNER управление админами
# =========================
@admin_router.message(lambda m: m.text and m.text.startswith("/addadmin"))
async def add_admin(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return await safe_send(message, "❌ Только owner")

    try:
        uid = int(message.text.split()[1])
    except:
        return await safe_send(message, "Формат: /addadmin id")

    admins = load_admins()
    admins = [int(x) for x in admins]

    if uid in admins:
        return await safe_send(message, "Он уже админ")

    admins.append(uid)
    save_admins(admins)
    await safe_send(message, f"✅ Админ выдан: {uid}")

@admin_router.message(lambda m: m.text and m.text.startswith("/deladmin"))
async def del_admin(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return await safe_send(message, "❌ Только owner")

    try:
        uid = int(message.text.split()[1])
    except:
        return await safe_send(message, "Формат: /deladmin id")

    admins = load_admins()
    admins = [int(x) for x in admins]

    if uid not in admins:
        return await safe_send(message, "Его нет в админах")

    admins.remove(uid)
    save_admins(admins)
    await safe_send(message, f"❌ Админ снят: {uid}")

# =========================
# СПИСОК АДМИНОВ
# =========================
@admin_router.message(lambda m: m.text == "/admins")
async def list_admins(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return

    admins = load_admins()
    if not admins:
        return await safe_send(message, "нет админов")

    text = "👑 Админы:\n\n"
    for aid in admins:
        try:
            user = await message.bot.get_chat(aid)
            username = f"@{user.username}" if user.username else "без юза"
            text += f"{username} | `{aid}`\n"
        except:
            text += f"не найден | `{aid}`\n"

    await safe_send(message, text, parse_mode="Markdown")

# =========================
# /id команда
# =========================
@admin_router.message(lambda m: m.text and m.text.startswith("/id"))
async def get_id(message: types.Message):
    try:
        if message.reply_to_message:
            uid = message.reply_to_message.from_user.id
            username = message.reply_to_message.from_user.username
            uname = f"@{username}" if username else "без юза"
            return await safe_send(message, f"👤 {uname}\nID: `{uid}`", parse_mode="Markdown")

        parts = message.text.split()

        if len(parts) >= 2:
            username = parts[1].replace("@", "")
            user = await message.bot.get_chat(username)
            uname = f"@{user.username}" if user.username else "без юза"
            return await safe_send(message, f"👤 {uname}\nID: `{user.id}`", parse_mode="Markdown")

        uid = message.from_user.id
        username = message.from_user.username
        uname = f"@{username}" if username else "без юза"
        await safe_send(message, f"👤 {uname}\nID: `{uid}`", parse_mode="Markdown")
    except:
        await safe_send(message, "❌ Ошибка получения ID")

# =========================
# JSON helpers
# =========================
def load_json(path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =========================
# Игроки
# =========================
def get_player(user_id: int):
    players = load_json(DB_PLAYERS)
    if str(user_id) not in players:
        players[str(user_id)] = {
            "user_id": user_id,
            "money": 0,
            "raf_coin": 0,
            "status": "Обычный"
        }
        save_json(DB_PLAYERS, players)
    return players[str(user_id)]

def save_player(user_id: int, data: dict):
    players = load_json(DB_PLAYERS)
    players[str(user_id)] = data
    save_json(DB_PLAYERS, players)

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
# Промокоды
# =========================
def load_promos():
    return load_json(PROMO_FILE)

def save_promos(data):
    save_json(PROMO_FILE, data)

# =========================
# Кнопки админки
# =========================
def admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Создать промокод", callback_data="admin_create_code")],
            [InlineKeyboardButton(text="📊 Стата", callback_data="admin_stats")],
            [InlineKeyboardButton(text="⚙️ Команды", callback_data="admin_commands")]
        ]
    )

# =========================
# Панель
# =========================
@admin_router.message(lambda m: m.text and m.text.lower() in ["админ", "панель"])
async def show_admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        return await safe_send(message, "❌ Нет доступа")
    await safe_send(message, "👑 Админ панель:", reply_markup=admin_keyboard())

# =========================
# Кнопки
# =========================
@admin_router.callback_query(lambda c: c.data.startswith("admin_"))
async def admin_callback(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await cb.answer("❌ Нет доступа", show_alert=True)

    text = {
        "admin_create_code": "📝 Формат:\n#код деньги 100\n#код raf 10\n#код статус VIP 1d",
        "admin_stats": "📊 Пока пусто",
        "admin_commands": "Создание промо: #код тип сумма\nтип: деньги / raf / статус"
    }.get(cb.data, "ошибка")

    await cb.message.edit_text(text, reply_markup=admin_keyboard())
    await cb.answer()

# =========================
# ПРОМО (админы могут создавать)
# =========================
@admin_router.message(lambda m: m.text and m.text.startswith("#"))
async def promo_handler(message: types.Message):
    try:
        user = message.from_user
        parts = message.text.strip().split()
        code = parts[0][1:].upper()

        promos = load_promos()

        # создание
        if is_admin(user.id) and len(parts) >= 3:
            if code in promos:
                return await safe_send(message, "❌ Такой промо уже есть")

            promo_type = parts[1].lower()
            value = parts[2]

            limit = None
            expires = None

            if len(parts) >= 4:
                arg = parts[3]
                if "d" in arg:
                    expires = (datetime.utcnow() + timedelta(days=int(arg.replace("d","")))).isoformat()
                elif arg.isdigit():
                    limit = int(arg)

            promos[code] = {
                "type": promo_type,
                "value": value,
                "limit": limit,
                "used": 0,
                "expires": expires
            }

            save_promos(promos)
            return await safe_send(message, f"✅ Промокод #{code} создан")

        # использование
        if code not in promos:
            return await safe_send(message, "❌ Промокод не найден")

        promo = promos[code]

        if promo.get("expires"):
            if datetime.fromisoformat(promo["expires"]) < datetime.utcnow():
                return await safe_send(message, "❌ Промо истёк")

        if promo.get("limit") and promo["used"] >= promo["limit"]:
            return await safe_send(message, "❌ Лимит исчерпан")

        player = get_player(user.id)

        if promo["type"] == "деньги":
            player["money"] += int(promo["value"])
            save_player(user.id, player)

        elif promo["type"] == "raf":
            raf = get_raf(user.id)
            raf["raf-coin"] += int(promo["value"])
            save_raf(user.id, raf)

        elif promo["type"] == "статус":
            player["status"] = promo["value"]
            save_player(user.id, player)

        promo["used"] += 1
        save_promos(promos)

        await safe_send(message, f"✅ Активирован #{code}")

    except Exception as e:
        print("PROMO ERROR:", e)
        await safe_send(message, "❌ Ошибка промокода")
