# Файл: commands/business/investbank.py

import json
import os
import time
import asyncio
from random import randint
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

invest_router = Router()

# ======================
# НАСТРОЙКИ
# ======================

INVEST_FILE = "database/investbank.json"
INVEST_PRICE = 1_000_000_000
STOCK_PRICE = 50_000_000  # инвестиционные пакеты

INVEST_UPGRADES = [
    {"level": 0, "income": 10_000_000, "max_stock": 5, "max_cash": 100_000_000, "price": 0},
    {"level": 1, "income": 19_000_000, "max_stock": 15, "max_cash": 150_200_000, "price": 150_000_000},
    {"level": 2, "income": 25_000_000, "max_stock": 30, "max_cash": 200_500_000, "price": 550_000_000},
    {"level": 3, "income": 30_000_000, "max_stock": 60, "max_cash": 500_000_000, "price": 800_000_000},
]

CYCLE_SECONDS = 3600  # 10 минут

# ======================
# БАЗА
# ======================

def load_invest():
    if not os.path.exists(INVEST_FILE):
        os.makedirs(os.path.dirname(INVEST_FILE), exist_ok=True)
        with open(INVEST_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(INVEST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_invest(data):
    with open(INVEST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_invest(user_id):
    data = load_invest()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {}

    if "bank" not in data[uid]:
        data[uid]["bank"] = {
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
        save_invest(data)

    level = data[uid]["bank"]["level"]
    upgrade = INVEST_UPGRADES[min(level, 3)]

    data[uid]["bank"]["income"] = upgrade["income"]
    data[uid]["bank"]["max_stock"] = upgrade["max_stock"]
    data[uid]["bank"]["max_cash"] = upgrade["max_cash"]

    return data[uid]["bank"]


def update_invest(user_id, bank):
    data = load_invest()
    uid = str(user_id)
    data[uid]["bank"] = bank
    save_invest(data)


# ======================
# КНОПКИ
# ======================

def invest_main_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏦 Открыть банк", callback_data=f"invest_open_{user_id}")],
        [InlineKeyboardButton(text="💼 Закупить пакеты", callback_data=f"invest_buy_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать доход", callback_data=f"invest_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"invest_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"invest_upgrades_{user_id}")]
    ])


def invest_back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"invest_back_{user_id}")]
    ])


def invest_upgrades_kb(bank, user_id):
    buttons = []
    if bank["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"invest_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"invest_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


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
# ЦИКЛ ДОХОДА
# ======================

async def invest_process_cycle(bot, user_id, bank):
    if bank["status"] != "active":
        return

    now = time.time()
    last = bank.get("last_cycle", now)
    cycles = int((now - last) // bank["cycle"])

    if cycles <= 0:
        return

    for _ in range(cycles):

        if bank["stock"] <= 0:
            bank["status"] = "closed"
            await bot.send_message(user_id, "⚠️ Банк закрыт: нет инвестиционных пакетов!")
            break

        if bank["cashbox"] >= bank["max_cash"]:
            bank["status"] = "closed"
            await bot.send_message(user_id, "💰 Касса банка заполнена, доход остановлен!")
            break

        gain = randint(0, bank["income"] * 2)

        bank["cashbox"] += gain
        bank["total_earned"] += gain
        bank["stock"] -= 1

        if bank["cashbox"] > bank["max_cash"]:
            bank["cashbox"] = bank["max_cash"]

    bank["last_cycle"] = now
    update_invest(user_id, bank)


# ======================
# ФОНОВЫЙ ВОРКЕР
# ======================

async def invest_background_worker(bot):
    while True:
        data = load_invest()
        for user_id in data.keys():
            bank = data[user_id].get("bank")
            if bank:
                await invest_process_cycle(bot, int(user_id), bank)
        await asyncio.sleep(60)


@invest_router.startup()
async def start_invest_background(bot):
    asyncio.create_task(invest_background_worker(bot))


# ======================
# ОБНОВЛЕНИЕ МЕНЮ
# ======================

async def refresh_invest_menu(call: types.CallbackQuery, bank):
    user_id = call.from_user.id

    status = "🟢 Открыт" if bank["status"] == "active" else "🔴 Закрыт"
    remaining = max(0, int(bank["cycle"] - (time.time() - bank.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🏦 ИНВЕСТБАНК\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {bank['level']}/3\n\n"
        f"💼 Пакеты: {bank['stock']} / {bank['max_stock']} (Цена: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {bank['cashbox']:,}$\n"
        f"💵 Доход: {bank['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await call.message.edit_text(text, reply_markup=invest_main_kb(user_id))


# ======================
# КОМАНДЫ
# ======================

@invest_router.message(F.text.lower() == "купить банк")
async def buy_bank(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    bank = get_invest(user_id)

    if bank["owned"]:
        await message.answer("⚠️ У вас уже есть ИнвестБанк 🏦!")
        return

    if player["money"] < INVEST_PRICE:
        await message.answer("❌ Недостаточно денег")
        return

    player["money"] -= INVEST_PRICE
    player.setdefault("business", []).append("🏦 ИнвестБанк")
    save_player(user_id, player)

    bank["owned"] = True
    update_invest(user_id, bank)

    await message.answer("🏦 ИнвестБанк куплен! Используйте команду 'Мой банк'")


@invest_router.message(F.text.lower() == "продать банк")
async def sell_bank(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    bank = get_invest(user_id)

    if not bank["owned"]:
        await message.answer("⚠️ У вас нет ИнвестБанка 🏦!")
        return

    refund = int(INVEST_PRICE * 0.75)
    player["money"] += refund

    if "🏦 ИнвестБанк" in player.get("business", []):
        player["business"].remove("🏦 ИнвестБанк")

    save_player(user_id, player)

    bank.update({
        "owned": False,
        "status": "closed",
        "level": 0,
        "stock": 0,
        "cashbox": 0,
        "total_earned": 0,
        "upgrades": 0
    })

    update_invest(user_id, bank)

    await message.answer(f"🏦 ИнвестБанк продан! Вы получили {refund:,}$")


@invest_router.message(F.text.lower() == "мой банк")
async def my_bank(message: types.Message):
    user_id = message.from_user.id
    bank = get_invest(user_id)

    if not bank["owned"]:
        await message.answer("⚠️ У вас нет ИнвестБанка 🏦!")
        return

    status = "🟢 Открыт" if bank["status"] == "active" else "🔴 Закрыт"
    remaining = max(0, int(bank["cycle"] - (time.time() - bank.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🏦 ИНВЕСТБАНК\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {bank['level']}/3\n\n"
        f"💼 Пакеты: {bank['stock']} / {bank['max_stock']} (Цена: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {bank['cashbox']:,}$\n"
        f"💵 Доход: {bank['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await message.answer(text, reply_markup=invest_main_kb(user_id))


# ======================
# CALLBACKS
# ======================

@invest_router.callback_query(F.data.startswith("invest_"))
async def invest_callbacks(call: types.CallbackQuery):
    if not await protect_owner(call):
        return

    user_id = call.from_user.id
    bank = get_invest(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data

    if data.startswith("invest_open_"):

        if bank["status"] == "active":
            await call.answer("Банк уже открыт!", show_alert=True)
            return

        if bank["stock"] <= 0:
            await call.answer("❌ Нет пакетов", show_alert=True)
            return

        bank["status"] = "active"
        bank["last_cycle"] = time.time()
        update_invest(user_id, bank)

        await call.answer("🏦 Банк открыт! Доход поступает 😎")
        await refresh_invest_menu(call, bank)

    elif data.startswith("invest_buy_"):

        if bank["stock"] >= bank["max_stock"]:
            await call.answer("⚠️ Склад заполнен", show_alert=True)
            return

        if player["money"] < STOCK_PRICE:
            await call.answer("❌ Недостаточно средств", show_alert=True)
            return

        player["money"] -= STOCK_PRICE
        bank["stock"] = bank["max_stock"]

        save_player(user_id, player)
        update_invest(user_id, bank)

        await call.answer("💼 Пакеты закуплены!", show_alert=True)
        await refresh_invest_menu(call, bank)

    elif data.startswith("invest_take_"):

        if bank["cashbox"] <= 0:
            await call.answer("⚠️ Касса пуста!", show_alert=True)
            return

        player["biz_account"] += bank["cashbox"]
        bank["cashbox"] = 0

        save_player(user_id, player)
        update_invest(user_id, bank)

        await call.answer("💰 Доход зачислен на бизнес счёт!", show_alert=True)
        await refresh_invest_menu(call, bank)

    elif data.startswith("invest_info_"):

        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = INVEST_UPGRADES[min(bank['level'], 3)]

        text = (
            "📊 СТАТУС ИНВЕСТБАНКА\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"🏦 Тип: ИнвестБанк\n"
            f"📈 Уровень: {bank['level']}/3\n"
            f"💼 Пакеты: {bank['stock']} / {upgrade['max_stock']}\n"
            f"💰 В кассе: {bank['cashbox']:,}$\n"
            f"💵 Доход: {upgrade['income']:,}$ / 1h\n\n"
            f"📊 Всего заработано: {bank['total_earned']:,}$\n"
            f"⬆ Улучшений: {bank['upgrades']}/3"
        )

        await call.message.edit_text(text, reply_markup=invest_back_kb(user_id))

    elif data.startswith("invest_back_"):
        await refresh_invest_menu(call, bank)

    elif data.startswith("invest_upgrades_") or data.startswith("invest_upgrade_"):

        level = bank["level"]

        if data.startswith("invest_upgrade_"):

            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return

            price = INVEST_UPGRADES[level + 1]["price"]

            if player["money"] < price:
                await call.answer("❌ Недостаточно денег", show_alert=True)
                return

            player["money"] -= price
            bank["level"] += 1
            bank["upgrades"] += 1

            upgrade = INVEST_UPGRADES[bank["level"]]
            bank["income"] = upgrade["income"]
            bank["max_stock"] = upgrade["max_stock"]
            bank["max_cash"] = upgrade["max_cash"]

            save_player(user_id, player)
            update_invest(user_id, bank)

            await call.answer("⬆ ИнвестБанк улучшен!", show_alert=True)

            level = bank["level"]

        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = INVEST_UPGRADES[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ ИНВЕСТБАНКА {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"💼 Пакеты: {next_upgrade['max_stock']}\n"
                f"💰 Максимальная касса: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )

        await call.message.edit_text(text, reply_markup=invest_upgrades_kb(bank, user_id))