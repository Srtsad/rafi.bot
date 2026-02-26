# Файл: commands/business/spaceport.py

import json
import os
import time
import asyncio
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

space_router = Router()

SPACE_FILE = "database/spaceport.json"
SPACE_PRICE = 6_000_000_000
STOCK_PRICE = 300_000_000
CYCLE_SECONDS = 3600  # 10 минут

SPACE_UPGRADES = [
    {"level": 0, "income": 80_000_000, "max_stock": 5, "max_cash": 800_000, "price": 0},
    {"level": 1, "income": 95_000_000, "max_stock": 15, "max_cash": 2_000_000_000, "price": 600_000_000},
    {"level": 2, "income": 110_000_000, "max_stock": 30, "max_cash": 4_000_000_000, "price": 800_000_000},
    {"level": 3, "income": 115_000_000, "max_stock": 60, "max_cash": 7_000_000_000, "price": 1_000_000_000},
]

# ======================
# БАЗА
# ======================

def load_space():
    if not os.path.exists(SPACE_FILE):
        os.makedirs(os.path.dirname(SPACE_FILE), exist_ok=True)
        with open(SPACE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(SPACE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_space(data):
    with open(SPACE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_space(user_id):
    data = load_space()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {}

    if "space" not in data[uid]:
        data[uid]["space"] = {
            "owned": False,
            "status": "closed",
            "level": 0,
            "stock": 0,
            "income": 80_000_000,
            "cycle": CYCLE_SECONDS,
            "last_cycle": 0,
            "cashbox": 0,
            "total_earned": 0,
            "upgrades": 0
        }
        save_space(data)

    level = data[uid]["space"]["level"]
    upgrade = SPACE_UPGRADES[min(level, 3)]

    data[uid]["space"]["income"] = upgrade["income"]
    data[uid]["space"]["max_stock"] = upgrade["max_stock"]
    data[uid]["space"]["max_cash"] = upgrade["max_cash"]

    return data[uid]["space"]

def update_space(user_id, space):
    data = load_space()
    uid = str(user_id)
    data[uid]["space"] = space
    save_space(data)

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

def space_main_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Запустить космопорт", callback_data=f"space_open_{user_id}")],
        [InlineKeyboardButton(text="🛒 Закупить ресурсы", callback_data=f"space_buy_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать доход", callback_data=f"space_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"space_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"space_upgrades_{user_id}")]
    ])

def space_back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"space_back_{user_id}")]
    ])

def space_upgrades_kb(user_id, space):
    buttons = []
    if space["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"space_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"space_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ======================
# ЦИКЛ ДОХОДА
# ======================

async def space_process_cycle(bot, user_id, space):
    if space["status"] != "active":
        return

    now = time.time()
    last = space.get("last_cycle", now)
    cycles = int((now - last) // space["cycle"])

    if cycles <= 0:
        return

    for _ in range(cycles):

        if space["stock"] <= 0:
            space["status"] = "closed"
            await bot.send_message(user_id, "⚠️ Космопорт остановлен: закончились ресурсы!")
            break

        if space["cashbox"] >= space["max_cash"]:
            space["status"] = "closed"
            await bot.send_message(user_id, "💰 Касса заполнена, работа приостановлена!")
            break

        space["stock"] -= 1
        space["cashbox"] += space["income"]
        space["total_earned"] += space["income"]

        if space["cashbox"] > space["max_cash"]:
            space["cashbox"] = space["max_cash"]

    space["last_cycle"] = now
    update_space(user_id, space)

# ======================
# ФОНОВЫЙ ВОРКЕР
# ======================

async def space_background_worker(bot):
    while True:
        data = load_space()
        for user_id in data.keys():
            space = data[user_id].get("space")
            if space:
                await space_process_cycle(bot, int(user_id), space)
        await asyncio.sleep(60)

@space_router.startup()
async def start_space_background(bot):
    asyncio.create_task(space_background_worker(bot))

# ======================
# ОБНОВЛЕНИЕ МЕНЮ
# ======================

async def refresh_space_menu(call: types.CallbackQuery, space):
    user_id = call.from_user.id

    status = "🟢 Активен" if space["status"] == "active" else "🔴 Закрыт"
    remaining = max(0, int(space["cycle"] - (time.time() - space.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🚀 КОСМОПОРТ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {space['level']}/3\n\n"
        f"🛒 Ресурсы: {space['stock']} / {space['max_stock']} (Цена: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {space['cashbox']:,}$\n"
        f"💵 Доход: {space['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await call.message.edit_text(text, reply_markup=space_main_kb(user_id))

# ======================
# КОМАНДЫ
# ======================

@space_router.message(F.text.lower().contains("купить космопорт"))
async def buy_space(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    space = get_space(user_id)

    if space["owned"]:
        await message.answer("⚠️ У вас уже есть Космопорт 🚀!")
        return

    if player["money"] < SPACE_PRICE:
        await message.answer("❌ Недостаточно денег")
        return

    player["money"] -= SPACE_PRICE
    player.setdefault("business", []).append("🚀 Космопорт")
    save_player(user_id, player)

    space["owned"] = True
    update_space(user_id, space)

    await message.answer("🚀 Космопорт куплен! Используйте 'Мой космопорт'")

@space_router.message(F.text.lower().contains("мой космопорт"))
async def my_space(message: types.Message):
    user_id = message.from_user.id
    space = get_space(user_id)

    if not space["owned"]:
        await message.answer("⚠️ У вас нет Космопорта 🚀!")
        return

    status = "🟢 Активен" if space["status"] == "active" else "🔴 Закрыт"
    remaining = max(0, int(space["cycle"] - (time.time() - space.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🚀 КОСМОПОРТ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {space['level']}/3\n\n"
        f"🛒 Ресурсы: {space['stock']} / {space['max_stock']} (Цена: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {space['cashbox']:,}$\n"
        f"💵 Доход: {space['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await message.answer(text, reply_markup=space_main_kb(user_id))

# ======================
# CALLBACKS
# ======================

@space_router.callback_query(F.data.startswith("space_"))
async def space_callbacks(call: types.CallbackQuery):

    if not await protect_owner(call):
        return

    user_id = call.from_user.id
    space = get_space(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data

    if data.startswith("space_open_"):

        if space["status"] == "active":
            await call.answer("Космопорт уже активен!", show_alert=True)
            return

        if space["stock"] <= 0:
            await call.answer("❌ Нет ресурсов", show_alert=True)
            return

        space["status"] = "active"
        space["last_cycle"] = time.time()
        update_space(user_id, space)

        await call.answer("🚀 Космопорт запущен!")
        await refresh_space_menu(call, space)

    elif data.startswith("space_buy_"):

        if space["stock"] >= space["max_stock"]:
            await call.answer("⚠️ Склад полон", show_alert=True)
            return

        if player["money"] < STOCK_PRICE:
            await call.answer("❌ Недостаточно денег", show_alert=True)
            return

        player["money"] -= STOCK_PRICE
        space["stock"] = space["max_stock"]

        save_player(user_id, player)
        update_space(user_id, space)

        await call.answer("🛒 Ресурсы закуплены!", show_alert=True)
        await refresh_space_menu(call, space)

    elif data.startswith("space_take_"):

        if space["cashbox"] <= 0:
            await call.answer("⚠️ Касса пуста!", show_alert=True)
            return

        player.setdefault("biz_account", 0)
        player["biz_account"] += space["cashbox"]
        space["cashbox"] = 0

        save_player(user_id, player)
        update_space(user_id, space)

        await call.answer("💰 Доход зачислен!", show_alert=True)
        await refresh_space_menu(call, space)

    elif data.startswith("space_info_"):

        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = SPACE_UPGRADES[min(space['level'], 3)]

        text = (
            "📊 СТАТУС КОСМОПОРТА\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"🏢 Тип: Космопорт 🚀\n"
            f"📈 Уровень: {space['level']}/3\n"
            f"🛒 Ресурсы: {space['stock']} / {upgrade['max_stock']}\n"
            f"💰 В кассе: {space['cashbox']:,}$\n"
            f"💵 Доход: {upgrade['income']:,}$ / 1h\n\n"
            f"📊 Всего заработано: {space['total_earned']:,}$\n"
            f"⬆ Улучшений: {space['upgrades']}/3"
        )

        await call.message.edit_text(text, reply_markup=space_back_kb(user_id))

    elif data.startswith("space_back_"):
        await refresh_space_menu(call, space)

    elif data.startswith("space_upgrades_") or data.startswith("space_upgrade_"):

        level = space["level"]

        if data.startswith("space_upgrade_"):

            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return

            price = SPACE_UPGRADES[level + 1]["price"]

            if player["money"] < price:
                await call.answer("❌ Недостаточно денег", show_alert=True)
                return

            player["money"] -= price
            space["level"] += 1
            space["upgrades"] += 1

            upgrade = SPACE_UPGRADES[space["level"]]
            space["income"] = upgrade["income"]
            space["max_stock"] = upgrade["max_stock"]
            space["max_cash"] = upgrade["max_cash"]

            save_player(user_id, player)
            update_space(user_id, space)

            await call.answer("⬆ Космопорт улучшен!", show_alert=True)

            level = space["level"]

        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = SPACE_UPGRADES[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ КОСМОПОРТА {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"🛒 Склад: {next_upgrade['max_stock']}\n"
                f"💰 Касса: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )

        await call.message.edit_text(text, reply_markup=space_upgrades_kb(user_id, space))