# Файл: commands/business/store.py

import json
import os
import time
import asyncio
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

store_router = Router()

STORE_FILE = "database/store24.json"
STORE_PRICE = 12_000_000
STOCK_PRICE = 400_000
CYCLE_SECONDS = 3600  # 10 минут

UPGRADES_STORE = [
    {"level": 0, "income": 50_000, "max_stock": 120, "max_cash": 70_000, "price": 0},
    {"level": 1, "income": 80_000, "max_stock": 250, "max_cash": 150_000, "price": 7_000_000},
    {"level": 2, "income": 120_000, "max_stock": 400, "max_cash": 300_000, "price": 12_000_000},
    {"level": 3, "income": 190_000, "max_stock": 600, "max_cash": 650_000, "price": 28_000_000},
]

# ======================
# БАЗА
# ======================

def load_store():
    if not os.path.exists(STORE_FILE):
        os.makedirs(os.path.dirname(STORE_FILE), exist_ok=True)
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(STORE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_store(data):
    with open(STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_store(user_id):
    data = load_store()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {}

    if "store" not in data[uid]:
        data[uid]["store"] = {
            "owned": False,
            "status": "closed",
            "level": 0,
            "stock": 0,
            "income": 50_000,
            "cycle": CYCLE_SECONDS,
            "last_cycle": 0,
            "cashbox": 0,
            "total_earned": 0,
            "upgrades": 0
        }
        save_store(data)

    level = data[uid]["store"]["level"]
    upgrade = UPGRADES_STORE[min(level, 3)]

    data[uid]["store"]["income"] = upgrade["income"]
    data[uid]["store"]["max_stock"] = upgrade["max_stock"]
    data[uid]["store"]["max_cash"] = upgrade["max_cash"]

    return data[uid]["store"]

def update_store(user_id, store):
    data = load_store()
    uid = str(user_id)
    data[uid]["store"] = store
    save_store(data)

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

def store_main_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶ Открыть магазин", callback_data=f"store_open_{user_id}")],
        [InlineKeyboardButton(text="📦 Закупить товар", callback_data=f"store_buy_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать выручку", callback_data=f"store_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"store_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"store_upgrades_{user_id}")]
    ])

def store_back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"store_back_{user_id}")]
    ])

def store_upgrades_kb(user_id, store):
    buttons = []
    if store["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"store_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"store_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ======================
# ЦИКЛ ДОХОДА (как в обычном магазине)
# ======================

async def store_process_cycle(bot, user_id, store):
    if store["status"] != "open":
        return

    now = time.time()
    last = store.get("last_cycle", now)
    cycles = int((now - last) // store["cycle"])

    if cycles <= 0:
        return

    for _ in range(cycles):

        if store["stock"] <= 0:
            store["status"] = "closed"
            await bot.send_message(user_id, "⚠️ Магазин остановлен: закончились товары!")
            break

        if store["cashbox"] >= store["max_cash"]:
            store["status"] = "closed"
            await bot.send_message(user_id, "💰 Касса заполнена, работа приостановлена!")
            break

        store["stock"] -= 1
        store["cashbox"] += store["income"]
        store["total_earned"] += store["income"]

        if store["cashbox"] > store["max_cash"]:
            store["cashbox"] = store["max_cash"]

    store["last_cycle"] = now
    update_store(user_id, store)

# ======================
# ФОНОВЫЙ ВОРКЕР
# ======================

async def store_background_worker(bot):
    while True:
        data = load_store()
        for user_id in data.keys():
            store = data[user_id].get("store")
            if store:
                await store_process_cycle(bot, int(user_id), store)
        await asyncio.sleep(60)

@store_router.startup()
async def start_store_background(bot):
    asyncio.create_task(store_background_worker(bot))

# ======================
# ОБНОВЛЕНИЕ МЕНЮ
# ======================

async def refresh_store_menu(call: types.CallbackQuery, store):
    user_id = call.from_user.id

    status = "🟢 Открыт" if store["status"] == "open" else "🔴 Закрыт"
    remaining = max(0, int(store["cycle"] - (time.time() - store.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🏬 МАГАЗИН 24/7\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {store['level']}/3\n\n"
        f"📦 Товар: {store['stock']} / {store['max_stock']} (Цена партии: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {store['cashbox']:,}$\n"
        f"💵 Доход: {store['income']:,}$ / 1h\n"
        f"⏱ Цикл продаж: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await call.message.edit_text(text, reply_markup=store_main_kb(user_id))

# ======================
# КОМАНДЫ
# ======================

@store_router.message(F.text.lower() == "купить магазин")
async def buy_store(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    store = get_store(user_id)

    if store["owned"]:
        await message.answer("⚠️ У вас уже есть магазин!")
        return

    if player["money"] < STORE_PRICE:
        await message.answer("🤡 Недостаточно денег")
        return

    player["money"] -= STORE_PRICE
    player.setdefault("business", []).append("🏬 Магазин 24/7")
    save_player(user_id, player)

    store["owned"] = True
    update_store(user_id, store)

    await message.answer("🏬 Магазин куплен!: Команда - Мой магазин")

@store_router.message(F.text.lower() == "продать магазин")
async def sell_store(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    store = get_store(user_id)

    if not store["owned"]:
        await message.answer("⚠️ У вас нет магазина!")
        return

    refund = int(STORE_PRICE * 0.75)
    player["money"] += refund

    if "🏬 Магазин 24/7" in player.get("business", []):
        player["business"].remove("🏬 Магазин 24/7")

    save_player(user_id, player)

    store.update({
        "owned": False,
        "status": "closed",
        "level": 0,
        "stock": 0,
        "cashbox": 0,
        "total_earned": 0,
        "upgrades": 0
    })

    update_store(user_id, store)

    await message.answer(f"🏬 Магазин продан! Вы получили {refund:,}$")

@store_router.message(F.text.lower() == "мой магазин")
async def my_store(message: types.Message):
    user_id = message.from_user.id
    store = get_store(user_id)

    if not store["owned"]:
        await message.answer("⚠️ У вас нет магазина!")
        return

    await store_process_cycle(message.bot, user_id, store)

    status = "🟢 Открыт" if store["status"] == "open" else "🔴 Закрыт"
    remaining = max(0, int(store["cycle"] - (time.time() - store.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🏬 МАГАЗИН 24/7\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {store['level']}/3\n\n"
        f"📦 Товар: {store['stock']} / {store['max_stock']} (Цена партии: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {store['cashbox']:,}$\n"
        f"💵 Доход: {store['income']:,}$ / 1h\n"
        f"⏱ Цикл продаж: 1h"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await message.answer(text, reply_markup=store_main_kb(user_id))

# ======================
# CALLBACKS
# ======================

@store_router.callback_query(F.data.startswith("store_"))
async def store_callbacks(call: types.CallbackQuery):

    if not await protect_owner(call):
        return

    user_id = call.from_user.id
    store = get_store(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data

    if data.startswith("store_open_"):

        if store["status"] == "open":
            await call.answer("Магазин уже открыт!", show_alert=True)
            return

        if store["stock"] <= 0:
            await call.answer("❌🤡 Нет товара", show_alert=True)
            return

        store["status"] = "open"
        store["last_cycle"] = time.time()
        update_store(user_id, store)

        await call.answer("▶ Магазин открыт! Клиенты пошли 😎")
        await refresh_store_menu(call, store)

    elif data.startswith("store_buy_"):

        if store["stock"] >= store["max_stock"]:
            await call.answer("⚠️ Уже полный склад", show_alert=True)
            return

        if player["money"] < STOCK_PRICE:
            await call.answer("❌🤡 Недостаточно средств", show_alert=True)
            return

        player["money"] -= STOCK_PRICE
        store["stock"] = store["max_stock"]

        save_player(user_id, player)
        update_store(user_id, store)

        await call.answer("📦 Товар закуплен!", show_alert=True)
        await refresh_store_menu(call, store)

    elif data.startswith("store_take_"):

        if store["cashbox"] <= 0:
            await call.answer("⚠️ Касса пусто!", show_alert=True)
            return

        player.setdefault("biz_account", 0)
        player["biz_account"] += store["cashbox"]
        store["cashbox"] = 0

        save_player(user_id, player)
        update_store(user_id, store)

        await call.answer("💰 Деньги зачислены на бизнес счёт", show_alert=True)
        await refresh_store_menu(call, store)

    elif data.startswith("store_info_"):

        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = UPGRADES_STORE[min(store['level'], 3)]

        text = (
            "📊 СТАТУС МАГАЗИНА\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"🏬 Тип: Магазин 24/7\n"
            f"📈 Уровень: {store['level']}/3\n"
            f"📦 Товар: {store['stock']} / {upgrade['max_stock']}\n"
            f"💰 В кассе: {store['cashbox']:,}$\n"
            f"💵 Доход: {upgrade['income']:,}$ / 1h\n\n"
            f"📊 Всего заработано: {store['total_earned']:,}$\n"
            f"⬆ Улучшений: {store['upgrades']}/3"
        )

        await call.message.edit_text(text, reply_markup=store_back_kb(user_id))

    elif data.startswith("store_back_"):
        await refresh_store_menu(call, store)

    elif data.startswith("store_upgrades_") or data.startswith("store_upgrade_"):

        level = store["level"]

        if data.startswith("store_upgrade_"):

            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return

            price = UPGRADES_STORE[level + 1]["price"]

            if player["money"] < price:
                await call.answer("❌ Недостаточно денег", show_alert=True)
                return

            player["money"] -= price
            store["level"] += 1
            store["upgrades"] += 1

            upgrade = UPGRADES_STORE[store["level"]]
            store["income"] = upgrade["income"]
            store["max_stock"] = upgrade["max_stock"]
            store["max_cash"] = upgrade["max_cash"]

            save_player(user_id, player)
            update_store(user_id, store)

            await call.answer("⬆ Магазин улучшен!", show_alert=True)

            level = store["level"]

        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = UPGRADES_STORE[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ МАГАЗИНА {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"📦 Склад: {next_upgrade['max_stock']}\n"
                f"💰 Касса: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )

        await call.message.edit_text(text, reply_markup=store_upgrades_kb(user_id, store))