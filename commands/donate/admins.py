import json
import os
from datetime import datetime, timedelta
from aiogram import Router, types

router = Router()

DB_PLAYERS = "database/players.json"
DB_DONATE = "database-donate/donate.json"
DB_ADMINS = "database/status/admins.json"

OWNER_ID = 852666681
STATUS_DURATION = timedelta(days=3650)

# =========================
# SAFE SEND
# =========================
async def safe(msg, text):
    try:
        await msg.answer(text)
    except:
        pass

# =========================
# JSON
# =========================
def load_json(path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path,"w",encoding="utf-8") as f:
            json.dump({},f)
    try:
        with open(path,"r",encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(path,data):
    with open(path,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=2,ensure_ascii=False)

# =========================
# Проверка Admins
# =========================
def is_admin(user_id:int):
    if user_id == OWNER_ID:
        return True
    admins = load_json(DB_ADMINS)
    return str(user_id) in admins

def add_admin(user_id:int):
    admins = load_json(DB_ADMINS)
    admins[str(user_id)] = {"id":user_id}
    save_json(DB_ADMINS,admins)

def remove_admin(user_id:int):
    admins = load_json(DB_ADMINS)
    if str(user_id) in admins:
        del admins[str(user_id)]
        save_json(DB_ADMINS,admins)

# =========================
# Игрок
# =========================
def get_player(uid:int):
    players = load_json(DB_PLAYERS)
    if str(uid) not in players:
        players[str(uid)] = {
            "user_id": uid,
            "username": f"Игрок {uid}",
            "money": 0,
            "status": None,
            "status_end": None
        }
        save_json(DB_PLAYERS,players)
    return players[str(uid)]

def save_player(uid:int,data:dict):
    players = load_json(DB_PLAYERS)
    players[str(uid)] = data
    save_json(DB_PLAYERS,players)

# =========================
# RAF
# =========================
def get_raf(uid:int):
    donate = load_json(DB_DONATE)
    if str(uid) not in donate:
        donate[str(uid)] = {"raf-coin":0}
        save_json(DB_DONATE,donate)
    return donate[str(uid)]

def save_raf(uid:int,data:dict):
    donate = load_json(DB_DONATE)
    donate[str(uid)] = data
    save_json(DB_DONATE,donate)

# =====================================================
# ВЫДАТЬ ADMIN (только owner)
# =====================================================
@router.message(lambda m: m.text and m.text.lower().startswith("выдать админ"))
async def give_admin(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return await safe(message,"❌ Только владелец")

    if not message.reply_to_message:
        return await safe(message,"Ответь на игрока")

    target = message.reply_to_message.from_user
    add_admin(target.id)

    player = get_player(target.id)
    player["status"] = "Admins"
    player["status_end"] = (datetime.utcnow()+STATUS_DURATION).isoformat()
    save_player(target.id,player)

    await safe(message,f"🛡️ {target.full_name} теперь Admin")

# =====================================================
# ЗАБРАТЬ ADMIN
# =====================================================
@router.message(lambda m: m.text and m.text.lower().startswith("забрать админ"))
async def remove_admin_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return await safe(message,"❌ Только владелец")

    if not message.reply_to_message:
        return await safe(message,"Ответь на игрока")

    target = message.reply_to_message.from_user
    remove_admin(target.id)

    player = get_player(target.id)
    player["status"] = None
    player["status_end"] = None
    save_player(target.id,player)

    await safe(message,"❌ Админ снят")

# =====================================================
# ВЫДАТЬ СТАТУС
# =====================================================
@router.message(lambda m: m.text and m.text.lower().startswith("выдать статус"))
async def give_status(message: types.Message):
    if not is_admin(message.from_user.id):
        return await safe(message,"❌ Нет доступа")

    if not message.reply_to_message:
        return await safe(message,"Ответь на игрока")

    args = message.text.split()
    if len(args) < 3:
        return await safe(message,"Пример: Выдать статус Gold")

    status_name = args[2]
    if status_name.lower() == "admins":
        return await safe(message,"❌ Нельзя выдать Admins")

    target = message.reply_to_message.from_user
    player = get_player(target.id)

    player["status"] = status_name
    player["status_end"] = (datetime.utcnow()+timedelta(days=15)).isoformat()
    save_player(target.id,player)

    await safe(message,f"✅ Выдан статус {status_name}")

# =====================================================
# ЗАБРАТЬ СТАТУС
# =====================================================
@router.message(lambda m: m.text and m.text.lower().startswith("забрать статус"))
async def remove_status(message: types.Message):
    if not is_admin(message.from_user.id):
        return await safe(message,"❌ Нет доступа")

    if not message.reply_to_message:
        return await safe(message,"Ответь на игрока")

    target = message.reply_to_message.from_user
    player = get_player(target.id)

    player["status"] = None
    player["status_end"] = None
    save_player(target.id,player)

    await safe(message,"❌ Статус снят")

# =====================================================
# ВЫДАТЬ COIN
# =====================================================
@router.message(lambda m: m.text and m.text.lower().startswith("выдать coin"))
async def give_coin(message: types.Message):
    if not is_admin(message.from_user.id):
        return await safe(message,"❌ Нет доступа")

    if not message.reply_to_message:
        return await safe(message,"Ответь на игрока")

    args = message.text.split()
    if len(args) < 3 or not args[2].isdigit():
        return await safe(message,"Пример: Выдать coin 500")

    amount = int(args[2])
    target = message.reply_to_message.from_user

    raf = get_raf(target.id)
    raf["raf-coin"] += amount
    save_raf(target.id,raf)

    await safe(message,f"💰 Выдано {amount} Raf")

# =====================================================
# ВЫДАТЬ ДЕНЬГИ
# =====================================================
@router.message(lambda m: m.text and m.text.lower().startswith("выдать деньги"))
async def give_money(message: types.Message):
    if not is_admin(message.from_user.id):
        return await safe(message,"❌ Нет доступа")

    if not message.reply_to_message:
        return await safe(message,"Ответь на игрока")

    args = message.text.split()
    if len(args) < 3 or not args[2].isdigit():
        return await safe(message,"Пример: Выдать деньги 500")

    amount = int(args[2])
    target = message.reply_to_message.from_user

    player = get_player(target.id)
    player["money"] += amount
    save_player(target.id,player)

    await safe(message,f"💸 Выдано {amount}")

# =====================================================
# ЗАБРАТЬ ДЕНЬГИ
# =====================================================
@router.message(lambda m: m.text and m.text.lower().startswith("забрать деньги"))
async def remove_money(message: types.Message):
    if not is_admin(message.from_user.id):
        return await safe(message,"❌ Нет доступа")

    if not message.reply_to_message:
        return await safe(message,"Ответь на игрока")

    args = message.text.split()
    if len(args) < 3 or not args[2].isdigit():
        return await safe(message,"Пример: Забрать деньги 500")

    amount = int(args[2])
    target = message.reply_to_message.from_user

    player = get_player(target.id)
    player["money"] = max(0, player.get("money",0)-amount)
    save_player(target.id,player)

    await safe(message,f"💸 Забрано {amount}")
