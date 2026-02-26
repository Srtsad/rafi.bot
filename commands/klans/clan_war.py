import json
import os
import random
import asyncio
from datetime import datetime

from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.helpers import get_player

router = Router()

CLAN_FILE = "commands/klans/klans.json"
WAR_FILE = "database/clan_wars.json"

MAX_BATTLE_MEMBERS = 10
CALL_TIMEOUT = 180


# =========================
# JSON
# =========================

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# =========================
# UTILS
# =========================

def get_clan_of(user_id):
    player = get_player(user_id)
    return str(player.get("clan_id") or "")


def get_strength(user_id):
    player = get_player(user_id)
    return player.get("exp", 0) if player else 0


def calc_total_power(members):
    base = sum(get_strength(uid) for uid in members)
    return int(base * random.uniform(0.95, 1.05))


def get_clan_leader(clan: dict):
    return clan.get("leader") or clan.get("owner")


# =========================
# СОСТАВ ПОКАЗАТЬ
# =========================

@router.message(F.text.lower() == "клан состав")
async def show_battle_squad(message: types.Message):
    clans = load_json(CLAN_FILE)
    clan_id = get_clan_of(message.from_user.id)

    if not clan_id or clan_id not in clans:
        return await message.answer("❌ Вы не в клане")

    clan = clans[clan_id]
    battle = clan.get("battle_members", [])

    sorted_members = sorted(
        battle,
        key=lambda uid: get_strength(uid),
        reverse=True
    )

    text = f'🏰 Клан "{clan["name"]}"\n'
    text += f"👥 Состав для битвы (макс {MAX_BATTLE_MEMBERS} человек):\n\n"

    total = 0
    for i, uid in enumerate(sorted_members, 1):
        player = get_player(uid)
        nickname = player.get("nickname") or f"Игрок {uid}"
        clickable_name = f"[{nickname}](tg://user?id={uid})"
        strength = player.get("exp", 0)
        total += strength
        text += f"{i}. {clickable_name} — {strength} опыта — `{uid}`\n"

    text += f"\nОбщая сила: {total}"

    await message.answer(text, parse_mode="Markdown")


# =========================
# ДОБАВИТЬ В СОСТАВ
# =========================

@router.message(F.text.startswith("состав принять"))
async def squad_add(message: types.Message):
    clans = load_json(CLAN_FILE)
    clan_id = get_clan_of(message.from_user.id)

    if not clan_id or clan_id not in clans:
        return await message.answer("❌ Вы не в клане")

    clan = clans[clan_id]
    leader_id = get_clan_leader(clan)

    if message.from_user.id != leader_id:
        return await message.answer("❌ Только лидер может менять состав")

    parts = message.text.split()
    if len(parts) < 3:
        return await message.answer("Формат: состав принять ID")

    try:
        uid = int(parts[2])
    except:
        return await message.answer("ID должен быть числом")

    if uid not in clan.get("members", []):
        return await message.answer("Игрок не состоит в клане")

    clan.setdefault("battle_members", [])

    if leader_id not in clan["battle_members"]:
        clan["battle_members"].append(leader_id)

    if uid in clan["battle_members"]:
        return await message.answer("Игрок уже в составе")

    if len(clan["battle_members"]) >= MAX_BATTLE_MEMBERS:
        return await message.answer("❌ Лимит 10 человек")

    clan["battle_members"].append(uid)
    save_json(CLAN_FILE, clans)

    await message.answer("✅ Игрок добавлен в боевой состав")


# =========================
# КИК ИЗ СОСТАВА
# =========================

@router.message(F.text.startswith("состав кик"))
async def squad_kick(message: types.Message):
    clans = load_json(CLAN_FILE)
    clan_id = get_clan_of(message.from_user.id)

    if not clan_id or clan_id not in clans:
        return await message.answer("❌ Вы не в клане")

    clan = clans[clan_id]
    leader_id = get_clan_leader(clan)

    if message.from_user.id != leader_id:
        return await message.answer("❌ Только лидер может менять состав")

    parts = message.text.split()
    if len(parts) < 3:
        return await message.answer("Формат: состав кик ID")

    try:
        uid = int(parts[2])
    except:
        return await message.answer("ID должен быть числом")

    if uid == leader_id:
        return await message.answer("❌ Лидера нельзя убрать из состава")

    if uid not in clan.get("battle_members", []):
        return await message.answer("Игрока нет в составе")

    clan["battle_members"].remove(uid)
    save_json(CLAN_FILE, clans)

    await message.answer("❌ Игрок удалён из состава")


# =========================
# ВЫЗОВ
# =========================
@router.message(F.text.startswith("клан вызов"))
async def clan_call(message: types.Message):
    clans = load_json(CLAN_FILE)
    clan_id = get_clan_of(message.from_user.id)

    if not clan_id or clan_id not in clans:
        return await message.answer("❌ Вы не в клане")

    clan = clans[clan_id]
    leader_id = get_clan_leader(clan)

    if message.from_user.id != leader_id:
        return await message.answer("❌ Только лидер может вызывать клан")

    parts = message.text.split()
    if len(parts) < 3:
        return await message.answer("⚠️ Формат: клан вызов ID_клана_противника")

    enemy_id = str(parts[2].strip())
    if enemy_id not in clans:
        return await message.answer("❌ Клан не найден")

    war_data = load_json(WAR_FILE)
    war_data["pending"] = {
        "attacker": clan_id,
        "defender": enemy_id,
        "money": 0,
        "rep": 0
    }
    save_json(WAR_FILE, war_data)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Деньги", callback_data="war_money")],
        [InlineKeyboardButton(text="🎖 Репутация", callback_data="war_rep")],
        [InlineKeyboardButton(text="⚔ Бой", callback_data="war_start")]
    ])

    await message.answer(f"🏰 Клан {clan['name']} вызвал клан {clans[enemy_id]['name']}!", reply_markup=kb)

# =========================
# КЛАНОВЫЙ ВЫЗОВ И БОЙ
# =========================

@router.message(F.text.startswith("клан вызов"))
async def clan_call(message: types.Message):
    clans = load_json(CLAN_FILE)
    clan_id = get_clan_of(message.from_user.id)
    if not clan_id or clan_id not in clans:
        return await message.answer("❌ Вы не в клане")

    clan = clans[clan_id]
    leader_id = get_clan_leader(clan)
    if message.from_user.id != leader_id:
        return await message.answer("❌ Только лидер может бросать вызов")

    try:
        enemy_id = message.text.split()[2]
    except:
        return await message.answer("⚠ Формат: клан вызов ID_клана_противника")

    if enemy_id not in clans:
        return await message.answer("❌ Клан не найден")

    # сохраняем pending бой
    war_data = {
        "attacker": clan_id,
        "defender": enemy_id,
        "money": 0,
        "rep": 0,
        "status": "pending",
        "last_set": None
    }
    save_json(WAR_FILE, war_data)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Деньги", callback_data="war_money")],
        [InlineKeyboardButton(text="🎖 Репутация", callback_data="war_rep")]
    ])
    await message.answer("Выберите тип ставки для боя:", reply_markup=kb)

    # уведомление защитников
    for uid in clans[enemy_id]["members"]:
        try:
            await message.bot.send_message(
                uid,
                f"📜 Ваш клан был вызван в бой!\n🏰 Клан {clan['name']} бросил вызов.\n⏳ 3 минуты на решение",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🛡 Принять",
                            callback_data=f"war_accept_{clan_id}_{enemy_id}"
                        ),
                        InlineKeyboardButton(
                            text="🚪 Отказаться",
                            callback_data=f"war_refuse_{clan_id}_{enemy_id}"
                        )
                    ]
                ])
            )
        except:
            pass


# =========================
# ВВОД СТАВКИ
# =========================

@router.callback_query(F.data == "war_money")
async def set_money(call: types.CallbackQuery):
    await call.message.answer("Введите сумму ставки (только число):")
    await call.answer()
    war_data = load_json(WAR_FILE)
    war_data["last_set"] = "money"
    save_json(WAR_FILE, war_data)

@router.callback_query(F.data == "war_rep")
async def set_rep(call: types.CallbackQuery):
    await call.message.answer("Введите ставку репутации (только число):")
    await call.answer()
    war_data = load_json(WAR_FILE)
    war_data["last_set"] = "rep"
    save_json(WAR_FILE, war_data)


# =========================
# ПРИНЯТЬ / ОТКАЗ
# =========================

@router.callback_query(F.data.startswith("war_accept"))
async def accept(call: types.CallbackQuery, bot):
    parts = call.data.split("_")
    if len(parts) < 4:
        return await call.answer("❌ Ошибка данных")

    atk, defn = parts[2], parts[3]
    war_data = load_json(WAR_FILE)
    if war_data.get("status") != "pending":
        return await call.answer("❌ Нет активного вызова")

    war_data["status"] = "accepted"
    save_json(WAR_FILE, war_data)

    clans = load_json(CLAN_FILE)
    # уведомляем участников
    for uid in clans[defn]["members"]:
        try:
            await bot.send_message(uid, f"⚔ Клан {clans[defn]['name']} принял вызов! Бой начинается!")
        except:
            pass
    for uid in clans[atk]["members"]:
        try:
            await bot.send_message(uid, f"⚔ Ваш вызов принят! Бой начинается!")
        except:
            pass

    await fight(atk, defn, bot)
    await call.answer()


@router.callback_query(F.data.startswith("war_refuse"))
async def refuse(call: types.CallbackQuery):
    parts = call.data.split("_")
    if len(parts) < 4:
        return await call.answer("❌ Ошибка данных")

    atk, defn = parts[2], parts[3]
    war_data = load_json(WAR_FILE)
    if war_data.get("status") != "pending":
        return await call.answer("❌ Нет активного вызова")

    clans = load_json(CLAN_FILE)

    # штраф за отказ
    if war_data.get("money", 0) > 0:
        clans[defn]["money"] = int(clans[defn].get("money",0) * 0.95)
        reason = "💰 -5% от казны"
    elif war_data.get("rep", 0) > 0:
        clans[defn]["reputation"] = int(clans[defn].get("reputation",0) * 0.95)
        reason = "🎖 Репутация -5%"
    else:
        reason = ""

    save_json(CLAN_FILE, clans)
    await call.message.answer(f"❌ Бой отклонён! {reason}")
    await call.answer()


# =========================
# ФУНКЦИЯ БОЯ
# =========================

async def fight(atk, defn, bot):
    clans = load_json(CLAN_FILE)
    war_data = load_json(WAR_FILE)

    atk_members = clans[atk].get("battle_members", [])
    def_members = clans[defn].get("battle_members", [])

    atk_power = calc_total_power(atk_members)
    def_power = calc_total_power(def_members)

    # случайные события
    event_roll = random.randint(1,3)
    if event_roll==1:
        atk_power*=0.95; def_power*=0.95; event="🌩 Гроза (-5% обеим)"
    elif event_roll==2:
        if atk_power<def_power: atk_power*=1.07
        else: def_power*=1.07
        event="🏹 Засада (+7% слабым)"
    else:
        if random.choice([True,False]): atk_power*=1.1
        else: def_power*=1.1
        event="👑 Боевой дух (+10%)"

    atk_power=int(atk_power)
    def_power=int(def_power)

    winner = atk if atk_power>def_power else defn
    loser = defn if winner==atk else atk

    reward_rep = war_data.get("rep",0)
    reward_money = war_data.get("money",0)

    clans[winner]["reputation"]+=reward_rep
    clans[loser]["reputation"]=max(int(clans[loser].get("reputation",0)-reward_rep*0.6),0)

    clans[winner]["money"]=clans[winner].get("money",0)+reward_money
    clans[loser]["money"]=max(clans[loser].get("money",0)-int(reward_money*0.6),0)

    save_json(CLAN_FILE, clans)

    # результат
    result=(
        f"🔥 ИТОГ БИТВЫ 🔥\n\n"
        f"{clans[atk]['name']} — {atk_power}\n"
        f"{clans[defn]['name']} — {def_power}\n\n"
        f"{event}\n\n"
        f"🏆 Победил: {clans[winner]['name']}\n"
        f"💰 Казна +{reward_money} / -{int(reward_money*0.6)}\n"
        f"🎖 Репутация +{reward_rep} / -{int(reward_rep*0.6)}"
    )

    all_members=list(set(atk_members+def_members))
    for uid in all_members:
        try:
            await bot.send_message(uid,result)
        except:
            pass

    # чистим WAR_FILE
    if os.path.exists(WAR_FILE):
        os.remove(WAR_FILE)