# commands/games/duel.py

import json
import os
import random
import asyncio
import time
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

duel_router = Router()

DUELS_FILE = "database/duels.json"
STATS_FILE = "database/duel_stats.json"
PLAYERS_FILE = "database/players.json"

# =========================
# Создание баз
# =========================
os.makedirs("database", exist_ok=True)
for f in [DUELS_FILE, STATS_FILE, PLAYERS_FILE]:
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as file:
            json.dump({}, file, ensure_ascii=False, indent=2)

# =========================
# Работа с JSON
# =========================
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# Игроки
# =========================
def get_player(user_id, username=None):
    players = load_json(PLAYERS_FILE)
    uid = str(user_id)
    if uid not in players:
        players[uid] = {
            "nickname": None,
            "username": username or f"Игрок {user_id}",
        }
        save_json(PLAYERS_FILE, players)
    return players[uid]

def get_mention(user_id):
    p = get_player(user_id)
    name = p.get("nickname") or p.get("username") or "Игрок"
    return f'<a href="tg://user?id={user_id}">{name}</a>'

# =========================
# Проверка сброса топа
# =========================
def check_reset():
    stats = load_json(STATS_FILE)
    now = time.time()
    if "_reset_time" not in stats:
        stats["_reset_time"] = now
        save_json(STATS_FILE, stats)
        return
    if now - stats["_reset_time"] >= 604800:
        stats.clear()
        stats["_reset_time"] = now
        save_json(STATS_FILE, stats)

def get_reset_minutes():
    stats = load_json(STATS_FILE)
    reset_time = stats.get("_reset_time", time.time())
    return max(0, int((604800 - (time.time() - reset_time)) // 60))

# =========================
# Проверка активной дуэли
# =========================
def user_in_duel(user_id):
    duels = load_json(DUELS_FILE)
    for d in duels.values():
        if d["status"] in ["wait", "fight"] and user_id in [d["p1"], d.get("p2")]:
            return True
    return False

# =========================
# Создание дуэли
# =========================
async def create_duel(message: types.Message, opponent=None):
    user = message.from_user

    if user_in_duel(user.id):
        return await message.answer("❌ Ты уже в дуэли")

    if opponent and user_in_duel(opponent.id):
        return await message.answer("❌ Игрок уже в дуэли")

    duel_id = str(int(time.time() * 1000))
    duel = {
        "p1": user.id,
        "p2": opponent.id if opponent else None,
        "hp1": 100,
        "hp2": 100,
        "turn": None,
        "aim": {},
        "dodge": {},
        "status": "wait",
        "time": time.time(),
        "last": time.time()
    }

    duels = load_json(DUELS_FILE)
    duels[duel_id] = duel
    save_json(DUELS_FILE, duels)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Принять", callback_data=f"d_ac_{duel_id}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"d_dc_{duel_id}")]
    ])

    if opponent:
        txt = f"⚔️ {get_mention(user.id)} вызывает {get_mention(opponent.id)}"
    else:
        txt = f"⚔️ {get_mention(user.id)} ищет соперника"

    await message.answer(txt + "\n⏳ 60 сек", reply_markup=kb, parse_mode="HTML")

    await asyncio.sleep(60)
    duels = load_json(DUELS_FILE)
    if duel_id in duels and duels[duel_id]["status"] == "wait":
        duels.pop(duel_id)
        save_json(DUELS_FILE, duels)
        await message.answer("⌛ Дуэль отменена")

# =========================
# Команды
# =========================
@duel_router.message(F.text.casefold().in_(["топ дуэлей", "топ дуэль"]))
async def duel_top(message: types.Message):
    check_reset()
    stats = load_json(STATS_FILE)
    stats.pop("_reset_time", None)
    if not stats:
        return await message.answer("😴 Нет побед")
    top = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]
    txt = "🏆 <b>ТОП ДУЭЛЯНТОВ</b>\n\n"
    for i, (uid, w) in enumerate(top, 1):
        txt += f"{i}. {get_mention(int(uid))} — {w}\n"
    txt += f"\n⏳ До сброса: {get_reset_minutes()} мин"
    await message.answer(txt, parse_mode="HTML")

@duel_router.message(F.text.casefold().startswith("дуэль"))
async def duel_start(message: types.Message):
    opponent = message.reply_to_message.from_user if message.reply_to_message else None
    await create_duel(message, opponent)

# =========================
# Callback
# =========================
@duel_router.callback_query(F.data.startswith("d_"))
async def duel_cb(call: CallbackQuery):
    data = call.data.split("_")
    act = data[1]
    duel_id = data[2]

    duels = load_json(DUELS_FILE)
    if duel_id not in duels:
        return await call.answer("❌ Нет")

    d = duels[duel_id]
    user = call.from_user

    # Принятие
    if act == "ac":
        if d["status"] == "fight":
            return await call.answer("❌ Дуэль уже началась")

        if d["p2"] and user.id != d["p2"]:
            return await call.answer("❌ Не твоя дуэль")

        if user_in_duel(user.id) and user.id not in [d["p1"], d.get("p2")]:
            return await call.answer("❌ Ты уже в дуэли")

        if not d["p2"]:
            d["p2"] = user.id

        d["status"] = "fight"
        d["turn"] = random.choice([d["p1"], d["p2"]])
        d["aim"] = {str(d["p1"]): 0, str(d["p2"]): 0}
        d["dodge"] = {str(d["p1"]): 0, str(d["p2"]): 0}
        d["last"] = time.time()

        save_json(DUELS_FILE, duels)

        await send_fight(call.message, duel_id, "🔥 Бой начался")
        asyncio.create_task(turn_timer(duel_id))
        return await call.answer()

    # Отмена
    if act == "dc":
        if user.id not in [d["p1"], d.get("p2")]:
            return await call.answer()
        duels.pop(duel_id)
        save_json(DUELS_FILE, duels)
        return await call.message.answer("❌ Дуэль отменена")

    # ===== БОЙ =====
    if d["status"] != "fight":
        return await call.answer()

    if user.id != d["turn"]:
        return await call.answer("❌ Не твой ход")

    p1, p2 = d["p1"], d["p2"]
    me_hp, en_hp = ("hp1", "hp2") if user.id == p1 else ("hp2", "hp1")
    enemy = p2 if user.id == p1 else p1
    txt = ""

    if act == "atk":
        chance = 70 + d["aim"][str(user.id)]
        d["aim"][str(user.id)] = 0
        if random.randint(1, 100) > chance:
            txt = "💨 Промах"
            dmg = 0
        else:
            roll = random.randint(1, 100)
            if roll <= 10:
                dmg = random.randint(45, 60)
                txt = f"💀 ХЕДШОТ −{dmg}"
            elif roll <= 35:
                dmg = random.randint(18, 28)
                txt = f"🎯 В тело −{dmg}"
            elif roll <= 65:
                dmg = random.randint(10, 18)
                txt = f"🦵 В ногу −{dmg}"
            else:
                dmg = random.randint(5, 14)
                txt = f"✋ В руку −{dmg}"

            if d["dodge"][str(enemy)] > 0 and random.randint(1, 100) < 50:
                txt = "🛡 Уклон!"
                dmg = 0

            d[en_hp] -= dmg
            d["dodge"][str(enemy)] = 0

    elif act == "aim":
        d["aim"][str(user.id)] += 25
        txt = "🎯 Прицелился (+шанс попадания в голову)"

    elif act == "heal":
        heal = random.randint(5, 20)
        txt = f"❤️ +{heal}"
        d[me_hp] = min(100, d[me_hp] + heal)

    elif act == "dodge":
        d["dodge"][str(user.id)] = 1
        txt = "🛡 Готовится уклониться"

    elif act == "stone":
        if random.randint(1, 100) <= 25:
            d["aim"][str(enemy)] = max(0, d["aim"][str(enemy)] - 25)
            txt = "🪨 Камень сбил прицел соперника! (-25% шанс попадания)"
        else:
            txt = "💨 Камень промахнулся"

    # Победа
    if d["hp1"] <= 0 or d["hp2"] <= 0:
        winner = user.id
        loser = enemy
        stats = load_json(STATS_FILE)
        check_reset()
        stats[str(winner)] = stats.get(str(winner), 0) + 1
        save_json(STATS_FILE, stats)
        duels.pop(duel_id)
        save_json(DUELS_FILE, duels)
        return await call.message.answer(
            f"🏆 Победитель: {get_mention(winner)}\n💀 Проиграл: {get_mention(loser)}",
            parse_mode="HTML"
        )

    d["turn"] = enemy
    d["last"] = time.time()
    save_json(DUELS_FILE, duels)
    await send_fight(call.message, duel_id, txt)
    await call.answer()

# =========================
# Функции боя
# =========================
async def send_fight(msg, duel_id, last=""):
    d = load_json(DUELS_FILE)[duel_id]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Атаковать", callback_data=f"d_atk_{duel_id}")],
        [InlineKeyboardButton(text="🎯 Прицел", callback_data=f"d_aim_{duel_id}")],
        [InlineKeyboardButton(text="❤️ Хилка", callback_data=f"d_heal_{duel_id}")],
        [InlineKeyboardButton(text="🛡 Уклон", callback_data=f"d_dodge_{duel_id}")],
        [InlineKeyboardButton(text="🪨 Кинуть камень", callback_data=f"d_stone_{duel_id}")]
    ])
    txt = (
        f"⚔️ ДУЭЛЬ\n\n"
        f"{get_mention(d['p1'])}: {d['hp1']} HP\n"
        f"{get_mention(d['p2'])}: {d['hp2']} HP\n\n"
        f"{last}\n"
        f"👉 Ход: {get_mention(d['turn'])}"
    )
    await msg.answer(txt, reply_markup=kb, parse_mode="HTML")

async def turn_timer(duel_id):
    await asyncio.sleep(120)
    duels = load_json(DUELS_FILE)
    if duel_id not in duels:
        return
    d = duels[duel_id]
    if time.time() - d["last"] < 120:
        return
    loser = d["turn"]
    winner = d["p2"] if loser == d["p1"] else d["p1"]
    stats = load_json(STATS_FILE)
    check_reset()
    stats[str(winner)] = stats.get(str(winner), 0) + 1
    save_json(STATS_FILE, stats)
    duels.pop(duel_id)
    save_json(DUELS_FILE, duels)