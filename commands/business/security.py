# Файл: commands/business/security_full.py

import json
import os
import time
import asyncio
from random import randint
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

security_router = Router()

SEC_FILE = "database/security.json"
SEC_PRICE = 20_000_000
STAFF_PRICE = 555_000
CYCLE_SECONDS = 600  # 10 минут

UPGRADES_SEC = [
    {"level": 0, "income": 100_000, "max_staff": 5, "max_cash": 80_000, "price": 0},
    {"level": 1, "income": 180_500, "max_staff": 10, "max_cash": 160_000, "price": 35_000_000},
    {"level": 2, "income": 220_000, "max_staff": 20, "max_cash": 350_000, "price": 45_000_000},
    {"level": 3, "income": 400_000, "max_staff": 30, "max_cash": 700_000, "price": 60_000_000},
]

# ======================
# БАЗА
# ======================

def load_sec():
    if not os.path.exists(SEC_FILE):
        os.makedirs(os.path.dirname(SEC_FILE), exist_ok=True)
        with open(SEC_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(SEC_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_sec(data):
    with open(SEC_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_sec(user_id):
    data = load_sec()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {}

    if "security" not in data[uid]:
        data[uid]["security"] = {
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
        save_sec(data)

    level = data[uid]["security"]["level"]
    upgrade = UPGRADES_SEC[min(level, 3)]

    data[uid]["security"]["income"] = upgrade["income"]
    data[uid]["security"]["max_staff"] = upgrade["max_staff"]
    data[uid]["security"]["max_cash"] = upgrade["max_cash"]

    return data[uid]["security"]

def update_sec(user_id, sec):
    data = load_sec()
    uid = str(user_id)
    data[uid]["security"] = sec
    save_sec(data)

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

def sec_main_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶ Активировать компанию", callback_data=f"sec_open_{user_id}")],
        [InlineKeyboardButton(text="👥 Нанять персонал", callback_data=f"sec_hire_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать выручку", callback_data=f"sec_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"sec_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"sec_upgrades_{user_id}")]
    ])

def sec_back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"sec_back_{user_id}")]
    ])

def sec_upgrades_kb(user_id, sec):
    buttons = []
    if sec["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"sec_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"sec_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ======================
# ЦИКЛ ДОХОДА
# ======================

async def sec_process_cycle(bot, user_id, sec):
    if sec["status"] != "active":
        return

    now = time.time()
    last = sec.get("last_cycle", now)
    cycles = int((now - last) // sec["cycle"])

    if cycles <= 0:
        return

    for _ in range(cycles):

        if sec["staff"] <= 0:
            sec["status"] = "closed"
            await bot.send_message(user_id, "⚠️ Компания остановлена: нет персонала!")
            break

        if sec["cashbox"] >= sec["max_cash"]:
            sec["status"] = "closed"
            await bot.send_message(user_id, "💰 Касса заполнена, работа остановлена!")
            break

        gain = randint(sec["income"] // 2, sec["income"] * 2)

        sec["cashbox"] += gain
        sec["total_earned"] += gain

        if sec["cashbox"] > sec["max_cash"]:
            sec["cashbox"] = sec["max_cash"]

    sec["last_cycle"] = now
    update_sec(user_id, sec)

# ======================
# ФОНОВЫЙ ВОРКЕР
# ======================

async def sec_background_worker(bot):
    while True:
        data = load_sec()
        for user_id in data.keys():
            sec = data[user_id].get("security")
            if sec:
                await sec_process_cycle(bot, int(user_id), sec)
        await asyncio.sleep(60)

@security_router.startup()
async def start_sec_background(bot):
    asyncio.create_task(sec_background_worker(bot))

# ======================
# ОБНОВЛЕНИЕ МЕНЮ
# ======================

async def refresh_sec_menu(call: types.CallbackQuery, sec):
    user_id = call.from_user.id

    status = "🟢 Активна" if sec["status"] == "active" else "🔴 Закрыта"
    remaining = max(0, int(sec["cycle"] - (time.time() - sec.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🛡 ОХРАННАЯ КОМПАНИЯ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {sec['level']}/3\n\n"
        f"👥 Персонал: {sec['staff']} / {sec['max_staff']} (Цена найма: {STAFF_PRICE:,}$)\n"
        f"💰 В кассе: {sec['cashbox']:,}$\n"
        f"💵 Доход: {sec['income']:,}$ / 10 мин\n"
        f"⏱ Цикл дохода: 10 мин\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await call.message.edit_text(text, reply_markup=sec_main_kb(user_id))

# ======================
# КОМАНДЫ
# ======================

@security_router.message(F.text.lower().contains("купить охранку"))
async def buy_sec(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    sec = get_sec(user_id)

    if sec["owned"]:
        await message.answer("⚠️ У вас уже есть охранная компания!")
        return

    if player["money"] < SEC_PRICE:
        await message.answer("❌ Недостаточно денег")
        return

    player["money"] -= SEC_PRICE
    player.setdefault("business", []).append("🛡 Охранная компания")
    save_player(user_id, player)

    sec["owned"] = True
    update_sec(user_id, sec)

    await message.answer("🛡 Компания куплена! Используйте 'Моя охранка'")

@security_router.message(F.text.lower().contains("моя охранка"))
async def my_sec(message: types.Message):
    user_id = message.from_user.id
    sec = get_sec(user_id)

    if not sec["owned"]:
        await message.answer("⚠️ У вас нет охранной компании!")
        return

    status = "🟢 Активна" if sec["status"] == "active" else "🔴 Закрыта"
    remaining = max(0, int(sec["cycle"] - (time.time() - sec.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🛡 ОХРАННАЯ КОМПАНИЯ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {sec['level']}/3\n\n"
        f"👥 Персонал: {sec['staff']} / {sec['max_staff']} (Цена найма: {STAFF_PRICE:,}$)\n"
        f"💰 В кассе: {sec['cashbox']:,}$\n"
        f"💵 Доход: {sec['income']:,}$ / 10 мин\n"
        f"⏱ Цикл дохода: 10 мин\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await message.answer(text, reply_markup=sec_main_kb(user_id))

# ======================
# CALLBACKS
# ======================

@security_router.callback_query(F.data.startswith("sec_"))
async def sec_callbacks(call: types.CallbackQuery):

    if not await protect_owner(call):
        return

    user_id = call.from_user.id
    sec = get_sec(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data

    if data.startswith("sec_open_"):

        if sec["status"] == "active":
            await call.answer("Компания уже активна!", show_alert=True)
            return

        if sec["staff"] <= 0:
            await call.answer("❌ Нет персонала", show_alert=True)
            return

        sec["status"] = "active"
        sec["last_cycle"] = time.time()
        update_sec(user_id, sec)

        await call.answer("▶ Компания активирована!", show_alert=True)
        await refresh_sec_menu(call, sec)

    elif data.startswith("sec_hire_"):

        if sec["staff"] >= sec["max_staff"]:
            await call.answer("⚠️ Максимальный персонал", show_alert=True)
            return

        if player["money"] < STAFF_PRICE:
            await call.answer("❌ Недостаточно денег", show_alert=True)
            return

        player["money"] -= STAFF_PRICE
        sec["staff"] = sec["max_staff"]

        save_player(user_id, player)
        update_sec(user_id, sec)

        await call.answer("👥 Персонал нанят!", show_alert=True)
        await refresh_sec_menu(call, sec)

    elif data.startswith("sec_take_"):

        if sec["cashbox"] <= 0:
            await call.answer("⚠️ Касса пуста!", show_alert=True)
            return

        player.setdefault("biz_account", 0)
        player["biz_account"] += sec["cashbox"]
        sec["cashbox"] = 0

        save_player(user_id, player)
        update_sec(user_id, sec)

        await call.answer("💰 Выручка зачислена!", show_alert=True)
        await refresh_sec_menu(call, sec)

    elif data.startswith("sec_info_"):

        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = UPGRADES_SEC[min(sec['level'], 3)]

        text = (
            "📊 СТАТУС ОХРАННОЙ КОМПАНИИ\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"🛡 Тип: Охранная компания\n"
            f"📈 Уровень: {sec['level']}/3\n"
            f"👥 Персонал: {sec['staff']} / {upgrade['max_staff']}\n"
            f"💰 В кассе: {sec['cashbox']:,}$\n"
            f"💵 Доход: {upgrade['income']:,}$ / 10 мин\n\n"
            f"📊 Всего заработано: {sec['total_earned']:,}$\n"
            f"⬆ Улучшений: {sec['upgrades']}/3"
        )

        await call.message.edit_text(text, reply_markup=sec_back_kb(user_id))

    elif data.startswith("sec_back_"):
        await refresh_sec_menu(call, sec)

    elif data.startswith("sec_upgrades_") or data.startswith("sec_upgrade_"):

        level = sec["level"]

        if data.startswith("sec_upgrade_"):

            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return

            price = UPGRADES_SEC[level + 1]["price"]

            if player["money"] < price:
                await call.answer("❌ Недостаточно денег", show_alert=True)
                return

            player["money"] -= price
            sec["level"] += 1
            sec["upgrades"] += 1

            upgrade = UPGRADES_SEC[sec["level"]]
            sec["income"] = upgrade["income"]
            sec["max_staff"] = upgrade["max_staff"]
            sec["max_cash"] = upgrade["max_cash"]

            save_player(user_id, player)
            update_sec(user_id, sec)

            await call.answer("⬆ Компания улучшена!", show_alert=True)

            level = sec["level"]

        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = UPGRADES_SEC[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ ОХРАННОЙ КОМПАНИИ {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"👥 Персонал: {next_upgrade['max_staff']}\n"
                f"💰 Касса: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )

        await call.message.edit_text(text, reply_markup=sec_upgrades_kb(user_id, sec))