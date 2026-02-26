# Файл: commands/business/nightclub.py

import json
import os
import time
import asyncio
from random import randint
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

router = Router()

CLUB_FILE = "database/nightclub.json"
CLUB_PRICE = 50_000_000
STAFF_PRICE = 500_000
CYCLE_SECONDS = 3600

UPGRADES_CLUB = [
    {"level": 0, "income": 100_000, "max_staff": 5, "max_cash": 100_000, "price": 0},
    {"level": 1, "income": 300_000, "max_staff": 10, "max_cash": 250_000, "price": 40_000_000},
    {"level": 2, "income": 460_000, "max_staff": 20, "max_cash": 1_000_000, "price": 85_000_000},
    {"level": 3, "income": 900_000, "max_staff": 35, "max_cash": 10_000_000, "price": 160_000_000},
]

# ======================
# БАЗА
# ======================

def load_club():
    if not os.path.exists(CLUB_FILE):
        os.makedirs(os.path.dirname(CLUB_FILE), exist_ok=True)
        with open(CLUB_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(CLUB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_club(data):
    with open(CLUB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_club(user_id):
    data = load_club()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {}

    if "club" not in data[uid]:
        data[uid]["club"] = {
            "owned": False,
            "status": "closed",
            "level": 0,
            "staff": 0,
            "income": 100_000,
            "cycle": CYCLE_SECONDS,
            "last_cycle": 0,
            "cashbox": 0,
            "total_earned": 0,
            "upgrades": 0
        }
        save_club(data)

    level = data[uid]["club"]["level"]
    upgrade = UPGRADES_CLUB[min(level, 3)]

    data[uid]["club"]["income"] = upgrade["income"]
    data[uid]["club"]["max_staff"] = upgrade["max_staff"]
    data[uid]["club"]["max_cash"] = upgrade["max_cash"]

    return data[uid]["club"]

def update_club(user_id, club):
    data = load_club()
    uid = str(user_id)
    data[uid]["club"] = club
    save_club(data)

# ======================
# ЗАЩИТА КНОПОК
# ======================

async def protect_owner(call: types.CallbackQuery) -> bool:
    if call.data and call.data.split("_")[-1].isdigit():
        owner_id = int(call.data.split("_")[-1])
        if call.from_user.id != owner_id:
            await call.answer("⛓ Это не ваша кнопка.", show_alert=True)
            return False
    return True

# ======================
# КНОПКИ
# ======================

def club_main_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶ Открыть клуб", callback_data=f"club_open_{user_id}")],
        [InlineKeyboardButton(text="👥 Нанять персонал", callback_data=f"club_hire_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать выручку", callback_data=f"club_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"club_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"club_upgrades_{user_id}")]
    ])

def club_back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"club_back_{user_id}")]
    ])

def club_upgrades_kb(user_id, club):
    buttons = []
    if club["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"club_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"club_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ======================
# ЦИКЛ ДОХОДА
# ======================

async def process_cycle(bot, user_id, club):
    if club["status"] != "active":
        return

    now = time.time()
    last = club.get("last_cycle", now)
    cycles = int((now - last) // club["cycle"])

    if cycles <= 0:
        return

    for _ in range(cycles):

        if club["staff"] <= 0:
            club["status"] = "closed"
            await bot.send_message(user_id, "⚠️ Клуб остановлен: нет персонала!")
            break

        if club["cashbox"] >= club["max_cash"]:
            club["status"] = "closed"
            await bot.send_message(user_id, "💰 Касса заполнена, доход остановлен!")
            break

        gain = randint(club["income"] // 2, club["income"] * 2)

        club["cashbox"] += gain
        club["total_earned"] += gain

        club["staff"] -= 1  # расход персонала

        if club["cashbox"] > club["max_cash"]:
            club["cashbox"] = club["max_cash"]

    club["last_cycle"] = now
    update_club(user_id, club)

# ======================
# ФОНОВЫЙ ВОРКЕР
# ======================

async def club_background_worker(bot):
    while True:
        data = load_club()
        for user_id in data.keys():
            club = data[user_id].get("club")
            if club:
                await process_cycle(bot, int(user_id), club)
        await asyncio.sleep(60)

@router.startup()
async def start_club_background(bot):
    asyncio.create_task(club_background_worker(bot))

# ======================
# ОБНОВЛЕНИЕ МЕНЮ
# ======================

async def refresh_menu(call: types.CallbackQuery, club):
    user_id = call.from_user.id

    status = "🟢 Открыт" if club["status"] == "active" else "🔴 Закрыт"
    remaining = max(0, int(club["cycle"] - (time.time() - club.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🎉 НОЧНОЙ КЛУБ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {club['level']}/3\n\n"
        f"👥 Персонал: {club['staff']} / {club['max_staff']} (Цена найма: {STAFF_PRICE:,}$)\n"
        f"💰 В кассе: {club['cashbox']:,}$\n"
        f"💵 Доход: {club['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await call.message.edit_text(text, reply_markup=club_main_kb(user_id))

# ======================
# КОМАНДЫ
# ======================

@router.message(F.text.lower().contains("купить клуб"))
async def buy_club(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    club = get_club(user_id)

    if club["owned"]:
        await message.answer("⚠️ У вас уже есть ночной клуб!")
        return

    if player["money"] < CLUB_PRICE:
        await message.answer("❌ Недостаточно денег")
        return

    player["money"] -= CLUB_PRICE
    player.setdefault("business", []).append("🎉 Ночной клуб")
    save_player(user_id, player)

    club["owned"] = True
    update_club(user_id, club)

    await message.answer("🎉 Ночной клуб куплен! Используйте 'Мой клуб'")

@router.message(F.text.lower().contains("продать клуб"))
async def sell_club(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    club = get_club(user_id)

    if not club["owned"]:
        await message.answer("⚠️ У вас нет ночного клуба!")
        return

    refund = int(CLUB_PRICE * 0.75)
    player["money"] += refund

    if "🎉 Ночной клуб" in player.get("business", []):
        player["business"].remove("🎉 Ночной клуб")

    save_player(user_id, player)

    club.update({
        "owned": False,
        "status": "closed",
        "level": 0,
        "staff": 0,
        "cashbox": 0,
        "total_earned": 0,
        "upgrades": 0
    })

    update_club(user_id, club)

    await message.answer(f"🎉 Ночной клуб продан! Вы получили {refund:,}$")

@router.message(F.text.lower().contains("мой клуб"))
async def my_club(message: types.Message):
    user_id = message.from_user.id
    club = get_club(user_id)

    if not club["owned"]:
        await message.answer("⚠️ У вас нет ночного клуба!")
        return

    status = "🟢 Открыт" if club["status"] == "active" else "🔴 Закрыт"
    remaining = max(0, int(club["cycle"] - (time.time() - club.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🎉 НОЧНОЙ КЛУБ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {club['level']}/3\n\n"
        f"👥 Персонал: {club['staff']} / {club['max_staff']} (Цена найма: {STAFF_PRICE:,}$)\n"
        f"💰 В кассе: {club['cashbox']:,}$\n"
        f"💵 Доход: {club['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await message.answer(text, reply_markup=club_main_kb(user_id))

# ======================
# CALLBACKS
# ======================

@router.callback_query(F.data.startswith("club_"))
async def club_callbacks(call: types.CallbackQuery):
    if not await protect_owner(call):
        return

    user_id = call.from_user.id
    club = get_club(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data

    if data.startswith("club_open_"):

        if club["status"] == "active":
            await call.answer("Клуб уже открыт!", show_alert=True)
            return

        if club["staff"] <= 0:
            await call.answer("❌ Нет персонала", show_alert=True)
            return

        club["status"] = "active"
        club["last_cycle"] = time.time()
        update_club(user_id, club)

        await call.answer("▶ Клуб открыт! 😎")
        await refresh_menu(call, club)

    elif data.startswith("club_hire_"):

        if club["staff"] >= club["max_staff"]:
            await call.answer("⚠️ Максимальный персонал", show_alert=True)
            return

        if player["money"] < STAFF_PRICE:
            await call.answer("❌ Недостаточно денег", show_alert=True)
            return

        player["money"] -= STAFF_PRICE
        club["staff"] = club["max_staff"]

        save_player(user_id, player)
        update_club(user_id, club)

        await call.answer("👥 Персонал нанят!", show_alert=True)
        await refresh_menu(call, club)

    elif data.startswith("club_take_"):

        if club["cashbox"] <= 0:
            await call.answer("⚠️ Касса пуста!", show_alert=True)
            return

        player["biz_account"] += club["cashbox"]
        club["cashbox"] = 0

        save_player(user_id, player)
        update_club(user_id, club)

        await call.answer("💰 Выручка зачислена!", show_alert=True)
        await refresh_menu(call, club)

    elif data.startswith("club_info_"):

        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = UPGRADES_CLUB[min(club['level'], 3)]

        text = (
            "📊 СТАТУС НОЧНОГО КЛУБА\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"🎉 Тип: Ночной клуб\n"
            f"📈 Уровень: {club['level']}/3\n"
            f"👥 Персонал: {club['staff']} / {upgrade['max_staff']}\n"
            f"💰 В кассе: {club['cashbox']:,}$\n"
            f"💵 Доход: {upgrade['income']:,}$ / 1h\n\n"
            f"📊 Всего заработано: {club['total_earned']:,}$\n"
            f"⬆ Улучшений: {club['upgrades']}/3"
        )

        await call.message.edit_text(text, reply_markup=club_back_kb(user_id))

    elif data.startswith("club_back_"):
        await refresh_menu(call, club)

    elif data.startswith("club_upgrades_") or data.startswith("club_upgrade_"):

        level = club["level"]

        if data.startswith("club_upgrade_"):

            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return

            price = UPGRADES_CLUB[level + 1]["price"]

            if player["money"] < price:
                await call.answer("❌ Недостаточно денег", show_alert=True)
                return

            player["money"] -= price
            club["level"] += 1
            club["upgrades"] += 1

            upgrade = UPGRADES_CLUB[club["level"]]
            club["income"] = upgrade["income"]
            club["max_staff"] = upgrade["max_staff"]
            club["max_cash"] = upgrade["max_cash"]

            save_player(user_id, player)
            update_club(user_id, club)

            await call.answer("⬆ Клуб улучшен!", show_alert=True)

            level = club["level"]

        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = UPGRADES_CLUB[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ НОЧНОГО КЛУБА {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"👥 Персонал: {next_upgrade['max_staff']}\n"
                f"💰 Касса: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )

        await call.message.edit_text(text, reply_markup=club_upgrades_kb(user_id, club))