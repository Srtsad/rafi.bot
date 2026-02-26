import json
import os
from datetime import datetime
from aiogram import Router, types, F

donate_router = Router()

DB_DONATE = "database-donate/donate.json"
DB_PLAYERS = "database/players.json"
DB_ADMINS = "database/status/admins.json"
OWNER_ID = 852666681  # владелец бота

# ----------------------
# JSON helpers
# ----------------------
def load_json(path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ----------------------
# Проверка админа
# ----------------------
def is_admin(user_id: int):
    if user_id == OWNER_ID:
        return True
    if not os.path.exists(DB_ADMINS):
        return False
    admins = load_json(DB_ADMINS)
    return str(user_id) in admins

# ----------------------
# Получить данные пользователя
# ----------------------
def get_donate(user: types.User):
    data = load_json(DB_DONATE)
    uid = str(user.id)

    if uid not in data:
        data[uid] = {
            "user_id": user.id,
            "nickname": user.full_name,
            "username": user.username or "",
            "tg_username": f"@{user.username}" if user.username else "",
            "last_nick_change": datetime.utcnow().isoformat(),
            "raf-coin": 0
        }
        save_json(DB_DONATE, data)
        return data[uid]

    changed = False
    user_data = data[uid]
    if "nickname" not in user_data or user_data["nickname"] != user.full_name:
        user_data["nickname"] = user.full_name
        user_data["last_nick_change"] = datetime.utcnow().isoformat()
        changed = True
    if "username" not in user_data or user_data["username"] != (user.username or ""):
        user_data["username"] = user.username or ""
        user_data["tg_username"] = f"@{user.username}" if user.username else ""
        changed = True
    if "raf-coin" not in user_data:
        user_data["raf-coin"] = 0
        changed = True

    if changed:
        data[uid] = user_data
        save_json(DB_DONATE, data)

    return user_data

def save_donate(user: types.User, user_data: dict):
    data = load_json(DB_DONATE)
    data[str(user.id)] = user_data
    save_json(DB_DONATE, data)

# ----------------------
# Команда /coin <@username или reply> <сумма>
# ----------------------
@donate_router.message(F.text.lower().startswith("/coin"))
async def give_coins(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У тебя нет прав на выдачу коинов")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Формат: /coin <@username или reply> <сумма>")
        return

    target_user = None
    amount = None

    # выдаём по reply
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        try:
            amount = int(args[1].replace("{", "").replace("}", ""))
        except:
            await message.answer("❌ Укажи корректное число")
            return
    else:
        # ищем username в players.json
        username_arg = args[1].lstrip("@").lower()
        players = load_json(DB_PLAYERS)
        found_user = None
        for uid, pdata in players.items():
            if pdata.get("username", "").lower() == username_arg or \
               (pdata.get("tg_username") or "").lower() == f"@{username_arg}":
                found_user = pdata
                break

        if not found_user:
            await message.answer(f"❌ Пользователь @{username_arg} не найден")
            return

        # создаём временный объект User
        class TempUser:
            def __init__(self, pdata):
                self.id = pdata["user_id"]
                self.full_name = pdata.get("nickname") or pdata.get("username") or f"Игрок {pdata['user_id']}"
                self.username = pdata.get("username")
        target_user = TempUser(found_user)

        # сумма должна быть 3-й аргумент
        if len(args) < 3:
            await message.answer("❌ Укажи сумму")
            return
        try:
            amount = int(args[2].replace("{", "").replace("}", ""))
        except:
            await message.answer("❌ Укажи корректное число")
            return

    # выдаём Raf-Coins
    user_data = get_donate(target_user)
    user_data["raf-coin"] += amount
    save_donate(target_user, user_data)

    await message.answer(
        f"💸 Выдано {amount} Raf-Coins\n"
        f"👤 Игрок: {user_data['nickname']}\n"
        f"🪙 Сейчас у него: {user_data['raf-coin']}\n"
        f"🔗 Telegram: {user_data['tg_username']}"
    )
