# Файл: commands/business/lab.py

import json
import os
import time
import asyncio
from random import randint
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

lab_router = Router()

LAB_FILE = "database/lab.json"
LAB_PRICE = 3_500_000_000
STOCK_PRICE = 100_000_000
CYCLE_SECONDS = 3600

LAB_UPGRADES = [
    {"level": 0, "income": 30_000_000, "max_stock": 5, "max_cash": 400_000_000, "price": 0},
    {"level": 1, "income": 50_000_000, "max_stock": 15, "max_cash": 600_000_000, "price": 500_000_000},
    {"level": 2, "income": 80_000_000, "max_stock": 30, "max_cash": 1_000_000_000, "price": 640_000_000},
    {"level": 3, "income": 100_000_000, "max_stock": 60, "max_cash": 2_000_000_000, "price": 1_000_000_000},
]

# ======================
# БАЗА
# ======================

def load_lab():
    if not os.path.exists(LAB_FILE):
        os.makedirs(os.path.dirname(LAB_FILE), exist_ok=True)
        with open(LAB_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(LAB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_lab(data):
    with open(LAB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_lab(user_id):
    data = load_lab()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {}

    if "lab" not in data[uid]:
        data[uid]["lab"] = {
            "owned": False,
            "status": "closed",
            "level": 0,
            "stock": 0,
            "income": 40_000,
            "cycle": CYCLE_SECONDS,
            "last_cycle": 0,
            "cashbox": 0,
            "total_earned": 0,
            "upgrades": 0
        }
        save_lab(data)

    level = data[uid]["lab"]["level"]
    upgrade = LAB_UPGRADES[min(level, 3)]

    data[uid]["lab"]["income"] = upgrade["income"]
    data[uid]["lab"]["max_stock"] = upgrade["max_stock"]
    data[uid]["lab"]["max_cash"] = upgrade["max_cash"]

    return data[uid]["lab"]

def update_lab(user_id, lab):
    data = load_lab()
    uid = str(user_id)
    data[uid]["lab"] = lab
    save_lab(data)

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

def lab_main_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔬 Открыть лабораторию", callback_data=f"lab_open_{user_id}")],
        [InlineKeyboardButton(text="💊 Закупить препараты", callback_data=f"lab_buy_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать доход", callback_data=f"lab_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"lab_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"lab_upgrades_{user_id}")]
    ])

def lab_back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"lab_back_{user_id}")]
    ])

def lab_upgrades_kb(user_id, lab):
    buttons = []
    if lab["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"lab_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"lab_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ======================
# ЦИКЛ ДОХОДА
# ======================

async def lab_process_cycle(bot, user_id, lab):
    if lab["status"] != "active":
        return

    now = time.time()
    last = lab.get("last_cycle", now)
    cycles = int((now - last) // lab["cycle"])

    if cycles <= 0:
        return

    for _ in range(cycles):

        if lab["stock"] <= 0:
            lab["status"] = "closed"
            await bot.send_message(user_id, "⚠️ Лаборатория остановлена: нет препаратов!")
            break

        if lab["cashbox"] >= lab["max_cash"]:
            lab["status"] = "closed"
            await bot.send_message(user_id, "💰 Касса заполнена, производство остановлено!")
            break

        gain = randint(lab["income"] // 2, lab["income"] * 2)

        lab["cashbox"] += gain
        lab["total_earned"] += gain
        lab["stock"] -= 1

        if lab["cashbox"] > lab["max_cash"]:
            lab["cashbox"] = lab["max_cash"]

    lab["last_cycle"] = now
    update_lab(user_id, lab)

# ======================
# ФОНОВЫЙ ВОРКЕР
# ======================

async def lab_background_worker(bot):
    while True:
        data = load_lab()
        for user_id in data.keys():
            lab = data[user_id].get("lab")
            if lab:
                await lab_process_cycle(bot, int(user_id), lab)
        await asyncio.sleep(60)

@lab_router.startup()
async def start_lab_background(bot):
    asyncio.create_task(lab_background_worker(bot))

# ======================
# ОБНОВЛЕНИЕ МЕНЮ
# ======================

async def refresh_lab_menu(call: types.CallbackQuery, lab):
    user_id = call.from_user.id

    status = "🟢 Открыта" if lab["status"] == "active" else "🔴 Закрыта"
    remaining = max(0, int(lab["cycle"] - (time.time() - lab.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🔬 ЛАБОРАТОРИЯ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {lab['level']}/3\n\n"
        f"💊 Препараты: {lab['stock']} / {lab['max_stock']} (Цена: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {lab['cashbox']:,}$\n"
        f"💵 Доход: {lab['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await call.message.edit_text(text, reply_markup=lab_main_kb(user_id))

# ======================
# КОМАНДЫ
# ======================

@lab_router.message(F.text.lower().contains("купить лабораторию"))
async def buy_lab(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    lab = get_lab(user_id)

    if lab["owned"]:
        await message.answer("⚠️ У вас уже есть Лаборатория 🔬!")
        return

    if player["money"] < LAB_PRICE:
        await message.answer("❌ Недостаточно денег")
        return

    player["money"] -= LAB_PRICE
    player.setdefault("business", []).append("🔬 Лаборатория")
    save_player(user_id, player)

    lab["owned"] = True
    update_lab(user_id, lab)

    await message.answer("🔬 Лаборатория куплена! Используйте 'Моя лаборатория'")

@lab_router.message(F.text.lower().contains("продать лабораторию"))
async def sell_lab(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    lab = get_lab(user_id)

    if not lab["owned"]:
        await message.answer("⚠️ У вас нет Лаборатории 🔬!")
        return

    refund = int(LAB_PRICE * 0.75)
    player["money"] += refund

    if "🔬 Лаборатория" in player.get("business", []):
        player["business"].remove("🔬 Лаборатория")

    save_player(user_id, player)

    lab.update({
        "owned": False,
        "status": "closed",
        "level": 0,
        "stock": 0,
        "cashbox": 0,
        "total_earned": 0,
        "upgrades": 0
    })

    update_lab(user_id, lab)

    await message.answer(f"🔬 Лаборатория продана! Вы получили {refund:,}$")

@lab_router.message(F.text.lower().contains("моя лаборатория"))
async def my_lab(message: types.Message):
    user_id = message.from_user.id
    lab = get_lab(user_id)

    if not lab["owned"]:
        await message.answer("⚠️ У вас нет Лаборатории 🔬!")
        return

    status = "🟢 Открыта" if lab["status"] == "active" else "🔴 Закрыта"
    remaining = max(0, int(lab["cycle"] - (time.time() - lab.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🔬 ЛАБОРАТОРИЯ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {lab['level']}/3\n\n"
        f"💊 Препараты: {lab['stock']} / {lab['max_stock']} (Цена: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {lab['cashbox']:,}$\n"
        f"💵 Доход: {lab['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await message.answer(text, reply_markup=lab_main_kb(user_id))

# ======================
# CALLBACKS
# ======================

@lab_router.callback_query(F.data.startswith("lab_"))
async def lab_callbacks(call: types.CallbackQuery):
    if not await protect_owner(call):
        return

    user_id = call.from_user.id
    lab = get_lab(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data

    if data.startswith("lab_open_"):

        if lab["status"] == "active":
            await call.answer("Лаборатория уже открыта!", show_alert=True)
            return

        if lab["stock"] <= 0:
            await call.answer("❌ Нет препаратов", show_alert=True)
            return

        lab["status"] = "active"
        lab["last_cycle"] = time.time()
        update_lab(user_id, lab)

        await call.answer("🔬 Лаборатория открыта! 🚀")
        await refresh_lab_menu(call, lab)

    elif data.startswith("lab_buy_"):

        if lab["stock"] >= lab["max_stock"]:
            await call.answer("⚠️ Склад полон", show_alert=True)
            return

        if player["money"] < STOCK_PRICE:
            await call.answer("❌ Недостаточно денег", show_alert=True)
            return

        player["money"] -= STOCK_PRICE
        lab["stock"] = lab["max_stock"]

        save_player(user_id, player)
        update_lab(user_id, lab)

        await call.answer("💊 Препараты закуплены!", show_alert=True)
        await refresh_lab_menu(call, lab)

    elif data.startswith("lab_take_"):

        if lab["cashbox"] <= 0:
            await call.answer("⚠️ Касса пуста!", show_alert=True)
            return

        player["biz_account"] += lab["cashbox"]
        lab["cashbox"] = 0

        save_player(user_id, player)
        update_lab(user_id, lab)

        await call.answer("💰 Доход зачислен!", show_alert=True)
        await refresh_lab_menu(call, lab)

    elif data.startswith("lab_info_"):

        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = LAB_UPGRADES[min(lab['level'], 3)]

        text = (
            "📊 СТАТУС ЛАБОРАТОРИИ\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"🔬 Тип: Лаборатория\n"
            f"📈 Уровень: {lab['level']}/3\n"
            f"💊 Препараты: {lab['stock']} / {upgrade['max_stock']}\n"
            f"💰 В кассе: {lab['cashbox']:,}$\n"
            f"💵 Доход: {upgrade['income']:,}$ / 1h\n\n"
            f"📊 Всего заработано: {lab['total_earned']:,}$\n"
            f"⬆ Улучшений: {lab['upgrades']}/3"
        )

        await call.message.edit_text(text, reply_markup=lab_back_kb(user_id))

    elif data.startswith("lab_back_"):
        await refresh_lab_menu(call, lab)

    elif data.startswith("lab_upgrades_") or data.startswith("lab_upgrade_"):

        level = lab["level"]

        if data.startswith("lab_upgrade_"):

            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return

            price = LAB_UPGRADES[level + 1]["price"]

            if player["money"] < price:
                await call.answer("❌ Недостаточно денег", show_alert=True)
                return

            player["money"] -= price
            lab["level"] += 1
            lab["upgrades"] += 1

            upgrade = LAB_UPGRADES[lab["level"]]
            lab["income"] = upgrade["income"]
            lab["max_stock"] = upgrade["max_stock"]
            lab["max_cash"] = upgrade["max_cash"]

            save_player(user_id, player)
            update_lab(user_id, lab)

            await call.answer("⬆ Лаборатория улучшена!", show_alert=True)

            level = lab["level"]

        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = LAB_UPGRADES[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ ЛАБОРАТОРИИ {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"💊 Склад: {next_upgrade['max_stock']}\n"
                f"💰 Касса: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )

        await call.message.edit_text(text, reply_markup=lab_upgrades_kb(user_id, lab))