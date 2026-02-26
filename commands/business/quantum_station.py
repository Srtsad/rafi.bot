# Файл: commands/business/quantum_station.py

import json
import os
import time
import asyncio
from random import randint
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

quantum_router = Router()

QUANTUM_FILE = "database/quantum_station.json"
QUANTUM_PRICE = 40_000_000_000
STOCK_PRICE = 500_000_000
CYCLE_SECONDS = 3600  # 1 час

QUANTUM_UPGRADES = [
    {"level": 0, "income": 200_000_000, "max_stock": 10, "max_cash": 8_000_000_000, "price": 0},
    {"level": 1, "income": 250_000_000, "max_stock": 20, "max_cash": 12_000_000_000, "price": 1_000_000_000},
    {"level": 2, "income": 350_000_000, "max_stock": 40, "max_cash": 18_000_000_000, "price": 3_000_000_000},
    {"level": 3, "income": 500_000_000, "max_stock": 80, "max_cash": 25_000_000_000, "price": 10_000_000_000},
]

# ======================
# БАЗА
# ======================

def load_quantum():
    if not os.path.exists(QUANTUM_FILE):
        os.makedirs(os.path.dirname(QUANTUM_FILE), exist_ok=True)
        with open(QUANTUM_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(QUANTUM_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_quantum(data):
    with open(QUANTUM_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_quantum(user_id):
    data = load_quantum()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {}

    if "quantum" not in data[uid]:
        data[uid]["quantum"] = {
            "owned": False,
            "status": "closed",
            "level": 0,
            "stock": 0,
            "income": 200_000_000,
            "cycle": CYCLE_SECONDS,
            "last_cycle": 0,
            "cashbox": 0,
            "total_earned": 0,
            "upgrades": 0
        }
        save_quantum(data)

    level = data[uid]["quantum"]["level"]
    upgrade = QUANTUM_UPGRADES[min(level, 3)]

    data[uid]["quantum"]["income"] = upgrade["income"]
    data[uid]["quantum"]["max_stock"] = upgrade["max_stock"]
    data[uid]["quantum"]["max_cash"] = upgrade["max_cash"]

    return data[uid]["quantum"]

def update_quantum(user_id, quantum):
    data = load_quantum()
    uid = str(user_id)
    data[uid]["quantum"] = quantum
    save_quantum(data)

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

def quantum_main_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Запустить станцию", callback_data=f"quantum_open_{user_id}")],
        [InlineKeyboardButton(text="🧪 Закупить ресурсы", callback_data=f"quantum_buy_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать доход", callback_data=f"quantum_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"quantum_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"quantum_upgrades_{user_id}")]
    ])

def quantum_back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"quantum_back_{user_id}")]
    ])

def quantum_upgrades_kb(user_id, quantum):
    buttons = []
    if quantum["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"quantum_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"quantum_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ======================
# ЦИКЛ ДОХОДА
# ======================

async def quantum_process_cycle(bot, user_id, quantum):
    if quantum["status"] != "active":
        return

    now = time.time()
    last = quantum.get("last_cycle", now)
    cycles = int((now - last) // quantum["cycle"])

    if cycles <= 0:
        return

    for _ in range(cycles):

        if quantum["stock"] <= 0:
            quantum["status"] = "closed"
            await bot.send_message(user_id, "⚠️ Станция остановлена: нет ресурсов!")
            break

        if quantum["cashbox"] >= quantum["max_cash"]:
            quantum["status"] = "closed"
            await bot.send_message(user_id, "💰 Касса заполнена, производство остановлено!")
            break

        gain = randint(quantum["income"] // 2, quantum["income"] * 2)

        quantum["cashbox"] += gain
        quantum["total_earned"] += gain
        quantum["stock"] -= 1

        if quantum["cashbox"] > quantum["max_cash"]:
            quantum["cashbox"] = quantum["max_cash"]

    quantum["last_cycle"] = now
    update_quantum(user_id, quantum)

# ======================
# ФОНОВЫЙ ВОРКЕР
# ======================

async def quantum_background_worker(bot):
    while True:
        data = load_quantum()
        for user_id in data.keys():
            quantum = data[user_id].get("quantum")
            if quantum:
                await quantum_process_cycle(bot, int(user_id), quantum)
        await asyncio.sleep(60)

@quantum_router.startup()
async def start_quantum_background(bot):
    asyncio.create_task(quantum_background_worker(bot))

# ======================
# ОБНОВЛЕНИЕ МЕНЮ
# ======================

async def refresh_quantum_menu(call: types.CallbackQuery, quantum):
    user_id = call.from_user.id

    status = "🟢 Активна" if quantum["status"] == "active" else "🔴 Выключена"
    remaining = max(0, int(quantum["cycle"] - (time.time() - quantum.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🚀 КВАНТОВАЯ СТАНЦИЯ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {quantum['level']}/3\n\n"
        f"🧪 Ресурсы: {quantum['stock']} / {quantum['max_stock']} (Цена: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {quantum['cashbox']:,}$\n"
        f"💵 Доход: {quantum['income']:,}$ / 1ч\n"
        f"⏱ Цикл дохода: 1ч\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await call.message.edit_text(text, reply_markup=quantum_main_kb(user_id))

# ======================
# КОМАНДЫ
# ======================

@quantum_router.message(F.text.lower().contains("купить станцию"))
async def buy_quantum(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    quantum = get_quantum(user_id)

    if quantum["owned"]:
        await message.answer("⚠️ У вас уже есть Квантовая станция 🚀!")
        return

    if player["money"] < QUANTUM_PRICE:
        await message.answer("❌ Недостаточно денег")
        return

    player["money"] -= QUANTUM_PRICE
    player.setdefault("business", []).append("🚀 Квантовая станция")
    save_player(user_id, player)

    quantum["owned"] = True
    update_quantum(user_id, quantum)

    await message.answer("🚀 Станция куплена! Используйте 'Моя станция'")

@quantum_router.message(F.text.lower().contains("моя станция"))
async def my_quantum(message: types.Message):
    user_id = message.from_user.id
    quantum = get_quantum(user_id)

    if not quantum["owned"]:
        await message.answer("⚠️ У вас нет Квантовой станции 🚀!")
        return

    status = "🟢 Активна" if quantum["status"] == "active" else "🔴 Выключена"
    remaining = max(0, int(quantum["cycle"] - (time.time() - quantum.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🚀 КВАНТОВАЯ СТАНЦИЯ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {quantum['level']}/3\n\n"
        f"🧪 Ресурсы: {quantum['stock']} / {quantum['max_stock']} (Цена: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {quantum['cashbox']:,}$\n"
        f"💵 Доход: {quantum['income']:,}$ / 1ч\n"
        f"⏱ Цикл дохода: 1ч\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await message.answer(text, reply_markup=quantum_main_kb(user_id))

# ======================
# CALLBACKS
# ======================

@quantum_router.callback_query(F.data.startswith("quantum_"))
async def quantum_callbacks(call: types.CallbackQuery):

    if not await protect_owner(call):
        return

    user_id = call.from_user.id
    quantum = get_quantum(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data

    if data.startswith("quantum_open_"):

        if quantum["status"] == "active":
            await call.answer("Станция уже активна!", show_alert=True)
            return

        if quantum["stock"] <= 0:
            await call.answer("❌ Нет ресурсов", show_alert=True)
            return

        quantum["status"] = "active"
        quantum["last_cycle"] = time.time()
        update_quantum(user_id, quantum)

        await call.answer("🚀 Станция запущена!")
        await refresh_quantum_menu(call, quantum)

    elif data.startswith("quantum_buy_"):

        if quantum["stock"] >= quantum["max_stock"]:
            await call.answer("⚠️ Склад полон", show_alert=True)
            return

        if player["money"] < STOCK_PRICE:
            await call.answer("❌ Недостаточно денег", show_alert=True)
            return

        player["money"] -= STOCK_PRICE
        quantum["stock"] = quantum["max_stock"]

        save_player(user_id, player)
        update_quantum(user_id, quantum)

        await call.answer("🧪 Ресурсы закуплены!", show_alert=True)
        await refresh_quantum_menu(call, quantum)

    elif data.startswith("quantum_take_"):

        if quantum["cashbox"] <= 0:
            await call.answer("⚠️ Касса пуста!", show_alert=True)
            return

        player.setdefault("biz_account", 0)
        player["biz_account"] += quantum["cashbox"]
        quantum["cashbox"] = 0

        save_player(user_id, player)
        update_quantum(user_id, quantum)

        await call.answer("💰 Доход зачислен!", show_alert=True)
        await refresh_quantum_menu(call, quantum)

    elif data.startswith("quantum_info_"):

        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = QUANTUM_UPGRADES[min(quantum['level'], 3)]

        text = (
            "📊 СТАТУС КВАНТОВОЙ СТАНЦИИ\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"🚀 Тип: Квантовая станция\n"
            f"📈 Уровень: {quantum['level']}/3\n"
            f"🧪 Ресурсы: {quantum['stock']} / {upgrade['max_stock']}\n"
            f"💰 В кассе: {quantum['cashbox']:,}$\n"
            f"💵 Доход: {upgrade['income']:,}$ / 1ч\n\n"
            f"📊 Всего заработано: {quantum['total_earned']:,}$\n"
            f"⬆ Улучшений: {quantum['upgrades']}/3"
        )

        await call.message.edit_text(text, reply_markup=quantum_back_kb(user_id))

    elif data.startswith("quantum_back_"):
        await refresh_quantum_menu(call, quantum)

    elif data.startswith("quantum_upgrades_") or data.startswith("quantum_upgrade_"):

        level = quantum["level"]

        if data.startswith("quantum_upgrade_"):

            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return

            price = QUANTUM_UPGRADES[level + 1]["price"]

            if player["money"] < price:
                await call.answer("❌ Недостаточно денег", show_alert=True)
                return

            player["money"] -= price
            quantum["level"] += 1
            quantum["upgrades"] += 1

            upgrade = QUANTUM_UPGRADES[quantum["level"]]
            quantum["income"] = upgrade["income"]
            quantum["max_stock"] = upgrade["max_stock"]
            quantum["max_cash"] = upgrade["max_cash"]

            save_player(user_id, player)
            update_quantum(user_id, quantum)

            await call.answer("⬆ Станция улучшена!", show_alert=True)

            level = quantum["level"]

        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = QUANTUM_UPGRADES[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ СТАНЦИИ {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"🧪 Склад: {next_upgrade['max_stock']}\n"
                f"💰 Касса: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )

        await call.message.edit_text(text, reply_markup=quantum_upgrades_kb(user_id, quantum))