# Файл: commands/business/larek.py

import json
import os
import time
import asyncio
from random import randint
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

larek_router = Router()

BIZ_FILE = "database/larek.json"
LAREK_PRICE = 5_000_000
STOCK_PRICE = 250_000
CYCLE_SECONDS = 3600

UPGRADES = [
    {"level": 0, "income": 25_000, "max_stock": 100, "max_cash": 50_000, "price": 0},
    {"level": 1, "income": 33_750, "max_stock": 200, "max_cash": 120_000, "price": 2_000_000},
    {"level": 2, "income": 45_500, "max_stock": 350, "max_cash": 250_000, "price": 6_000_000},
    {"level": 3, "income": 61_000, "max_stock": 550, "max_cash": 600_000, "price": 12_000_000},
]

# ======================
# БАЗА
# ======================

def load_larek():
    if not os.path.exists(BIZ_FILE):
        os.makedirs(os.path.dirname(BIZ_FILE), exist_ok=True)
        with open(BIZ_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(BIZ_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_larek(data):
    with open(BIZ_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_larek(user_id):
    data = load_larek()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {}

    if "larek" not in data[uid]:
        data[uid]["larek"] = {
            "owned": False,
            "status": "stopped",
            "level": 0,
            "stock": 0,
            "income": 4000,
            "cycle": CYCLE_SECONDS,
            "last_cycle": 0,
            "cashbox": 0,
            "total_earned": 0,
            "upgrades": 0
        }
        save_larek(data)

    level = data[uid]["larek"]["level"]
    upgrade = UPGRADES[min(level, 3)]

    data[uid]["larek"]["income"] = upgrade["income"]
    data[uid]["larek"]["max_stock"] = upgrade["max_stock"]
    data[uid]["larek"]["max_cash"] = upgrade["max_cash"]

    return data[uid]["larek"]

def update_larek(user_id, larek):
    data = load_larek()
    uid = str(user_id)
    data[uid]["larek"] = larek
    save_larek(data)

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

def main_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶ Открыть ларёк", callback_data=f"larek_open_{user_id}")],
        [InlineKeyboardButton(text="📦 Закупить товар", callback_data=f"larek_buy_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать выручку", callback_data=f"larek_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"larek_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"larek_upgrades_{user_id}")]
    ])

def back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"larek_back_{user_id}")]
    ])

def upgrades_kb(user_id, larek):
    buttons = []
    if larek["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"larek_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"larek_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ======================
# ЦИКЛ ПРОДАЖ
# ======================

async def process_cycle(bot, user_id, larek):
    if larek["status"] != "working":
        return

    now = time.time()
    last = larek.get("last_cycle", now)
    cycles = int((now - last) // larek["cycle"])

    if cycles <= 0:
        return

    for _ in range(cycles):

        if larek["stock"] <= 0:
            larek["status"] = "stopped"
            await bot.send_message(user_id, "⚠️ Ларёк остановлен: нет товара!")
            break

        if larek["cashbox"] >= larek["max_cash"]:
            larek["status"] = "stopped"
            await bot.send_message(user_id, "💰 Касса заполнена, продажи остановлены!")
            break

        gain = randint(larek["income"] // 2, larek["income"] * 2)

        larek["cashbox"] += gain
        larek["total_earned"] += gain
        larek["stock"] -= 1

        if larek["cashbox"] > larek["max_cash"]:
            larek["cashbox"] = larek["max_cash"]

    larek["last_cycle"] = now
    update_larek(user_id, larek)

# ======================
# ФОНОВЫЙ ВОРКЕР
# ======================

async def larek_background_worker(bot):
    while True:
        data = load_larek()
        for user_id in data.keys():
            larek = data[user_id].get("larek")
            if larek:
                await process_cycle(bot, int(user_id), larek)
        await asyncio.sleep(60)

@larek_router.startup()
async def start_larek_background(bot):
    asyncio.create_task(larek_background_worker(bot))

# ======================
# ОБНОВЛЕНИЕ МЕНЮ
# ======================

async def refresh_menu(call: types.CallbackQuery, larek):
    user_id = call.from_user.id

    status = "🟢 Открыт" if larek["status"] == "working" else "🔴 Закрыт"
    remaining = max(0, int(larek["cycle"] - (time.time() - larek.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🏪 ЛАРЁК «МОЙ ЛАРЁК»\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {larek['level']}/3\n\n"
        f"📦 Товар: {larek['stock']} / {larek['max_stock']} (Цена партии: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {larek['cashbox']:,}$\n"
        f"💵 Доход: {larek['income']:,}$ / 1h\n"
        f"⏱ Цикл продаж: 1h\n"
        f"⏳ До следующего запуска: {minutes:02d}:{seconds:02d}"
    )

    await call.message.edit_text(text, reply_markup=main_kb(user_id))

# ======================
# КОМАНДЫ
# ======================

@larek_router.message(F.text.lower().contains("купить ларёк"))
async def buy_larek(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    larek = get_larek(user_id)

    if larek["owned"]:
        await message.answer("⚠️ У вас уже есть ларёк!")
        return

    if player["money"] < LAREK_PRICE:
        await message.answer("🤡 Недостаточно денег")
        return

    player["money"] -= LAREK_PRICE
    player.setdefault("business", []).append("🏪 Ларёк")
    save_player(user_id, player)

    larek["owned"] = True
    update_larek(user_id, larek)

    await message.answer("🏪 Ларёк куплен! Используйте 'Мой ларёк'")

@larek_router.message(F.text.lower().contains("продать ларёк"))
async def sell_larek(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    larek = get_larek(user_id)

    if not larek["owned"]:
        await message.answer("⚠🤡 У вас нет ларька!")
        return

    refund = int(LAREK_PRICE * 0.75)
    player["money"] += refund

    if "🏪 Ларёк" in player.get("business", []):
        player["business"].remove("🏪 Ларёк")

    save_player(user_id, player)

    larek.update({
        "owned": False,
        "status": "stopped",
        "level": 0,
        "stock": 0,
        "cashbox": 0,
        "total_earned": 0,
        "upgrades": 0
    })

    update_larek(user_id, larek)

    await message.answer(f"🏪 Ларёк продан! Вы получили {refund:,}$")

@larek_router.message(F.text.lower().contains("мой ларёк"))
async def my_larek(message: types.Message):
    user_id = message.from_user.id
    larek = get_larek(user_id)

    if not larek["owned"]:
        await message.answer("⚠🤡 У вас нет ларька!")
        return

    status = "🟢 Открыт" if larek["status"] == "working" else "🔴 Закрыт"
    remaining = max(0, int(larek["cycle"] - (time.time() - larek.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🏪 ЛАРЁК «МОЙ ЛАРЁК»\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {larek['level']}/3\n\n"
        f"📦 Товар: {larek['stock']} / {larek['max_stock']} (Цена партии: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {larek['cashbox']:,}$\n"
        f"💵 Доход: {larek['income']:,}$ / 1h\n"
        f"⏱ Цикл продаж: 1h\n"
        f"⏳ До следующего запуска: {minutes:02d}:{seconds:02d}"
    )

    await message.answer(text, reply_markup=main_kb(user_id))

# ======================
# CALLBACKS
# ======================

@larek_router.callback_query(F.data.startswith("larek_"))
async def larek_callbacks(call: types.CallbackQuery):
    if not await protect_owner(call):
        return

    user_id = call.from_user.id
    larek = get_larek(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data

    if data.startswith("larek_open_"):

        if larek["status"] == "working":
            await call.answer("Ларёк уже открыт!", show_alert=True)
            return

        if larek["stock"] <= 0:
            await call.answer("❌ Нет товара", show_alert=True)
            return

        larek["status"] = "working"
        larek["last_cycle"] = time.time()
        update_larek(user_id, larek)

        await call.answer("▶ Ларёк открыт! 😎")
        await refresh_menu(call, larek)

    elif data.startswith("larek_buy_"):

        if larek["stock"] >= larek["max_stock"]:
            await call.answer("⚠️ Уже полный склад", show_alert=True)
            return

        if player["money"] < STOCK_PRICE:
            await call.answer("🤡 Недостаточно средств", show_alert=True)
            return

        player["money"] -= STOCK_PRICE
        larek["stock"] = larek["max_stock"]

        save_player(user_id, player)
        update_larek(user_id, larek)

        await call.answer("📦 Товар закуплен!", show_alert=True)
        await refresh_menu(call, larek)

    elif data.startswith("larek_take_"):

        if larek["cashbox"] <= 0:
            await call.answer("⚠️ Касса пуста!", show_alert=True)
            return

        player["biz_account"] += larek["cashbox"]
        larek["cashbox"] = 0

        save_player(user_id, player)
        update_larek(user_id, larek)

        await call.answer("💰 Выручка зачислена!", show_alert=True)
        await refresh_menu(call, larek)

    elif data.startswith("larek_info_"):

        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = UPGRADES[min(larek['level'], 3)]

        text = (
            "📊 СТАТУС ЛАРЬКА\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"🏪 Тип: Ларёк\n"
            f"📈 Уровень: {larek['level']}/3\n"
            f"📦 Товар: {larek['stock']} / {upgrade['max_stock']}\n"
            f"💰 В кассе: {larek['cashbox']:,}$\n"
            f"💵 Доход: {upgrade['income']:,}$ / 1h\n\n"
            f"📊 Всего заработано: {larek['total_earned']:,}$\n"
            f"⬆ Улучшений: {larek['upgrades']}/3"
        )

        await call.message.edit_text(text, reply_markup=back_kb(user_id))

    elif data.startswith("larek_back_"):
        await refresh_menu(call, larek)

    elif data.startswith("larek_upgrades_") or data.startswith("larek_upgrade_"):

        level = larek["level"]

        if data.startswith("larek_upgrade_"):

            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return

            price = UPGRADES[level + 1]["price"]

            if player["money"] < price:
                await call.answer("🤡 Недостаточно денег", show_alert=True)
                return

            player["money"] -= price
            larek["level"] += 1
            larek["upgrades"] += 1

            upgrade = UPGRADES[larek["level"]]
            larek["income"] = upgrade["income"]
            larek["max_stock"] = upgrade["max_stock"]
            larek["max_cash"] = upgrade["max_cash"]

            save_player(user_id, player)
            update_larek(user_id, larek)

            await call.answer("⬆ Ларёк улучшен!", show_alert=True)

            level = larek["level"]

        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = UPGRADES[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ «МОЙ ЛАРЁК» {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"📦 Склад: {next_upgrade['max_stock']}\n"
                f"💰 Касса: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )

        await call.message.edit_text(text, reply_markup=upgrades_kb(user_id, larek))