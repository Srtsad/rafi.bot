import json
import os
from aiogram import Router, types
from datetime import datetime

router = Router()

DB_PLAYERS = "database/players.json"
DB_ADMINS = "database/status/admins.json"
OWNER_ID = 852666681  # владелец бота

# ----------------------
# JSON helpers
# ----------------------
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ----------------------
# Проверка на админа
# ----------------------
def is_admin(user_id: int):
    if user_id == OWNER_ID:
        return True
    if not os.path.exists(DB_ADMINS):
        return False
    admins = load_json(DB_ADMINS)
    return str(user_id) in admins

# ----------------------
# Игроки
# ----------------------
def get_player(user_id: int):
    players = load_json(DB_PLAYERS)
    if str(user_id) not in players:
        players[str(user_id)] = {
            "user_id": user_id,
            "username": f"Игрок {user_id}",
            "tg_username": "",
            "money": 0
        }
        save_json(DB_PLAYERS, players)
    return players[str(user_id)]

def save_player(user_id: int, data: dict):
    players = load_json(DB_PLAYERS)
    players[str(user_id)] = data
    save_json(DB_PLAYERS, players)

# ----------------------
# Команда: Выдать деньги
# ----------------------
@router.message(lambda message: message.text and message.text.lower().startswith("выдать деньги"))
async def give_money(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У тебя нет прав выдавать деньги")
        return

    target = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        target = get_player(target_user.id)
        target_id = target_user.id
    else:
        args = message.text.strip().split()
        if len(args) < 3:
            await message.answer("❌ Формат: Выдать деньги <username/ответ> <сумма>")
            return
        username = args[2].lstrip("@").lower()
        players = load_json(DB_PLAYERS)
        for uid, pdata in players.items():
            if pdata.get("username", "").lower() == username or (pdata.get("tg_username") or "").lower() == f"@{username}":
                target = pdata
                target_id = int(uid)
                break
        if not target:
            await message.answer(f"❌ Пользователь {username} не найден")
            return

    # Сумма
    args = message.text.strip().split()
    if message.reply_to_message:
        if len(args) < 3 or not args[-1].isdigit():
            await message.answer("❌ Формат: Выдать деньги <сумма> (через reply)")
            return
        amount = int(args[-1])
    else:
        if not args[-1].isdigit():
            await message.answer("❌ Сумма должна быть числом")
            return
        amount = int(args[-1])

    if amount <= 0:
        await message.answer("❌ Сумма должна быть больше нуля")
        return

    # Добавляем деньги
    target["money"] = target.get("money", 0) + amount
    save_player(target_id, target)

    await message.answer(
        f"✅ Игроку {target.get('username','—')} выдано 💸 {amount:,} монет.\n"
        f"💰 Сейчас у него {target['money']:,} монет"
    )

# ----------------------
# Команда: Забрать деньги
# ----------------------
@router.message(lambda message: message.text and message.text.lower().startswith("забрать деньги"))
async def remove_money(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У тебя нет прав забирать деньги")
        return

    target = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        target = get_player(target_user.id)
        target_id = target_user.id
    else:
        args = message.text.strip().split()
        if len(args) < 3:
            await message.answer("❌ Формат: Забрать деньги <username/ответ> <сумма/всё>")
            return
        username = args[2].lstrip("@").lower()
        players = load_json(DB_PLAYERS)
        for uid, pdata in players.items():
            if pdata.get("username", "").lower() == username or (pdata.get("tg_username") or "").lower() == f"@{username}":
                target = pdata
                target_id = int(uid)
                break
        if not target:
            await message.answer(f"❌ Пользователь {username} не найден")
            return

    # Сумма
    args = message.text.strip().split()
    if message.reply_to_message:
        if len(args) < 3:
            await message.answer("❌ Формат: Забрать деньги <сумма> (через reply)")
            return
        amount_arg = args[-1]
    else:
        amount_arg = args[-1]

    if amount_arg.lower() == "всё":
        amount = target.get("money", 0)
    elif amount_arg.isdigit():
        amount = int(amount_arg)
    else:
        await message.answer("❌ Сумма должна быть числом или 'всё'")
        return

    if amount <= 0:
        await message.answer("❌ Сумма должна быть больше нуля")
        return

    target["money"] = max(target.get("money", 0) - amount, 0)
    save_player(target_id, target)

    await message.answer(
        f"✅ У игрока {target.get('username','—')} забрано 💸 {amount:,} монет.\n"
        f"💰 Сейчас у него {target['money']:,} монет"
    )
