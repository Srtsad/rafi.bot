# Файл: commands/business/yachtclub.py

import json
import os
import time
import asyncio
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

yacht_router = Router()

YACHT_FILE = "database/yachtclub.json"
YACHT_PRICE = 500_000_000
STOCK_PRICE = 12_000_000
CYCLE_SECONDS = 3600  # 10 минут

YACHT_UPGRADES = [
    {"level": 0, "income": 1_000_000, "max_stock": 10, "max_cash": 3_000_000, "price": 0},
    {"level": 1, "income": 2_000_000, "max_stock": 25, "max_cash": 10_000_000, "price": 50_000_000},
    {"level": 2, "income": 5_050_000, "max_stock": 50, "max_cash": 50_500_000, "price": 100_000_000},
    {"level": 3, "income": 8_000_000, "max_stock": 100, "max_cash": 70_000_000, "price": 350_000_000},
]

# ======================
# БАЗА
# ======================

def load_yacht():
    if not os.path.exists(YACHT_FILE):
        os.makedirs(os.path.dirname(YACHT_FILE), exist_ok=True)
        with open(YACHT_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(YACHT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_yacht(data):
    with open(YACHT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_yacht(user_id):
    data = load_yacht()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {}

    if "yacht" not in data[uid]:
        data[uid]["yacht"] = {
            "owned": False,
            "status": "closed",
            "level": 0,
            "stock": 0,
            "income": YACHT_UPGRADES[0]["income"],
            "cycle": CYCLE_SECONDS,
            "last_cycle": 0,
            "cashbox": 0,
            "total_earned": 0,
            "upgrades": 0
        }
        save_yacht(data)

    level = data[uid]["yacht"]["level"]
    upgrade = YACHT_UPGRADES[min(level, 3)]

    data[uid]["yacht"]["income"] = upgrade["income"]
    data[uid]["yacht"]["max_stock"] = upgrade["max_stock"]
    data[uid]["yacht"]["max_cash"] = upgrade["max_cash"]

    return data[uid]["yacht"]

def update_yacht(user_id, yacht):
    data = load_yacht()
    uid = str(user_id)
    data[uid]["yacht"] = yacht
    save_yacht(data)

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

def yacht_main_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⛵ Открыть клуб", callback_data=f"yacht_open_{user_id}")],
        [InlineKeyboardButton(text="🎟 Закупить пропуска", callback_data=f"yacht_buy_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать выручку", callback_data=f"yacht_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"yacht_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"yacht_upgrades_{user_id}")]
    ])

def yacht_back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"yacht_back_{user_id}")]
    ])

def yacht_upgrades_kb(user_id, yacht):
    buttons = []
    if yacht["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"yacht_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"yacht_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ======================
# ЦИКЛ ДОХОДА (фоновый)
# ======================

async def yacht_process_cycle(bot, user_id, yacht):
    if yacht["status"] != "active":
        return

    now = time.time()
    last = yacht.get("last_cycle", now)
    cycles = int((now - last) // yacht["cycle"])

    if cycles <= 0:
        return

    for _ in range(cycles):

        if yacht["stock"] <= 0:
            yacht["status"] = "closed"
            await bot.send_message(user_id, "⚠️ Клуб закрыт: закончились пропуска!")
            break

        if yacht["cashbox"] >= yacht["max_cash"]:
            yacht["status"] = "closed"
            await bot.send_message(user_id, "💰 Касса заполнена, работа приостановлена!")
            break

        yacht["stock"] -= 1
        yacht["cashbox"] += yacht["income"]
        yacht["total_earned"] += yacht["income"]

        if yacht["cashbox"] > yacht["max_cash"]:
            yacht["cashbox"] = yacht["max_cash"]

    yacht["last_cycle"] = now
    update_yacht(user_id, yacht)

async def yacht_background_worker(bot):
    while True:
        data = load_yacht()
        for user_id in data.keys():
            yacht = data[user_id].get("yacht")
            if yacht:
                await yacht_process_cycle(bot, int(user_id), yacht)
        await asyncio.sleep(60)

@yacht_router.startup()
async def start_yacht_background(bot):
    asyncio.create_task(yacht_background_worker(bot))

# ======================
# ОБНОВЛЕНИЕ МЕНЮ
# ======================

async def refresh_yacht_menu(call: types.CallbackQuery, yacht):
    user_id = call.from_user.id

    status = "🟢 Открыт" if yacht["status"] == "active" else "🔴 Закрыт"
    remaining = max(0, int(yacht["cycle"] - (time.time() - yacht.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"⛵ ЯХТ-КЛУБ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {yacht['level']}/3\n\n"
        f"🎟 Пропуска: {yacht['stock']} / {yacht['max_stock']} (Цена: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {yacht['cashbox']:,}$\n"
        f"💵 Доход: {yacht['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await call.message.edit_text(text, reply_markup=yacht_main_kb(user_id))

# ======================
# КОМАНДЫ
# ======================

@yacht_router.message(F.text.lower() == "купить яхт клуб")
async def buy_yacht(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    yacht = get_yacht(user_id)

    if yacht["owned"]:
        await message.answer("⚠️ У вас уже есть яхт-клуб ⛵!")
        return

    if player["money"] < YACHT_PRICE:
        await message.answer("❌ Недостаточно денег")
        return

    player["money"] -= YACHT_PRICE
    player.setdefault("business", []).append("⛵ Яхт-клуб")
    save_player(user_id, player)

    yacht["owned"] = True
    update_yacht(user_id, yacht)

    await message.answer("⛵ Яхт-клуб куплен!: Команда - Мой яхт клуб")

@yacht_router.message(F.text.lower() == "продать яхт клуб")
async def sell_yacht(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    yacht = get_yacht(user_id)

    if not yacht["owned"]:
        await message.answer("⚠️ У вас нет яхт-клуба ⛵!")
        return

    refund = int(YACHT_PRICE * 0.75)
    player["money"] += refund

    if "⛵ Яхт-клуб" in player.get("business", []):
        player["business"].remove("⛵ Яхт-клуб")

    save_player(user_id, player)

    yacht.update({
        "owned": False,
        "status": "closed",
        "level": 0,
        "stock": 0,
        "cashbox": 0,
        "total_earned": 0,
        "upgrades": 0
    })

    update_yacht(user_id, yacht)

    await message.answer(f"⛵ Яхт-клуб продан! Вы получили {refund:,}$")

@yacht_router.message(F.text.lower() == "мой яхт клуб")
async def my_yacht(message: types.Message):
    user_id = message.from_user.id
    yacht = get_yacht(user_id)

    if not yacht["owned"]:
        await message.answer("⚠️ У вас нет яхт-клуба ⛵!")
        return

    await yacht_process_cycle(message.bot, user_id, yacht)

    status = "🟢 Открыт" if yacht["status"] == "active" else "🔴 Закрыт"
    remaining = max(0, int(yacht["cycle"] - (time.time() - yacht.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"⛵ ЯХТ-КЛУБ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {yacht['level']}/3\n\n"
        f"🎟 Пропуска: {yacht['stock']} / {yacht['max_stock']} (Цена: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {yacht['cashbox']:,}$\n"
        f"💵 Доход: {yacht['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await message.answer(text, reply_markup=yacht_main_kb(user_id))

# ======================
# CALLBACKS
# ======================

@yacht_router.callback_query(F.data.startswith("yacht_"))
async def yacht_callbacks(call: types.CallbackQuery):

    if not await protect_owner(call):
        return

    user_id = call.from_user.id
    yacht = get_yacht(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data

    if data.startswith("yacht_open_"):

        if yacht["status"] == "active":
            await call.answer("Клуб уже открыт!", show_alert=True)
            return

        if yacht["stock"] <= 0:
            await call.answer("❌ Нет пропусков", show_alert=True)
            return

        yacht["status"] = "active"
        yacht["last_cycle"] = time.time()
        update_yacht(user_id, yacht)

        await call.answer("⛵ Клуб открыт! Гости приходят 😎")
        await refresh_yacht_menu(call, yacht)

    elif data.startswith("yacht_buy_"):

        if yacht["stock"] >= yacht["max_stock"]:
            await call.answer("⚠️ Уже полный клуб", show_alert=True)
            return

        if player["money"] < STOCK_PRICE:
            await call.answer("❌ Недостаточно средств", show_alert=True)
            return

        player["money"] -= STOCK_PRICE
        yacht["stock"] = yacht["max_stock"]

        save_player(user_id, player)
        update_yacht(user_id, yacht)

        await call.answer("🎟 Пропуска закуплены!", show_alert=True)
        await refresh_yacht_menu(call, yacht)

    elif data.startswith("yacht_take_"):

        if yacht["cashbox"] <= 0:
            await call.answer("⚠️ Касса пуста!", show_alert=True)
            return

        player.setdefault("biz_account", 0)
        player["biz_account"] += yacht["cashbox"]
        yacht["cashbox"] = 0

        save_player(user_id, player)
        update_yacht(user_id, yacht)

        await call.answer("💰 Деньги зачислены на бизнес счёт", show_alert=True)
        await refresh_yacht_menu(call, yacht)

    elif data.startswith("yacht_info_"):

        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = YACHT_UPGRADES[min(yacht['level'], 3)]

        text = (
            "📊 СТАТУС ЯХТ-КЛУБА\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"⛵ Тип: Яхт-клуб\n"
            f"📈 Уровень: {yacht['level']}/3\n"
            f"🎟 Пропуска: {yacht['stock']} / {upgrade['max_stock']}\n"
            f"💰 В кассе: {yacht['cashbox']:,}$\n"
            f"💵 Доход: {upgrade['income']:,}$ / 1h\n\n"
            f"📊 Всего заработано: {yacht['total_earned']:,}$\n"
            f"⬆ Улучшений: {yacht['upgrades']}/3"
        )

        await call.message.edit_text(text, reply_markup=yacht_back_kb(user_id))

    elif data.startswith("yacht_back_"):
        await refresh_yacht_menu(call, yacht)

    elif data.startswith("yacht_upgrades_") or data.startswith("yacht_upgrade_"):

        level = yacht["level"]

        if data.startswith("yacht_upgrade_"):

            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return

            price = YACHT_UPGRADES[level + 1]["price"]

            if player["money"] < price:
                await call.answer("❌ Недостаточно денег", show_alert=True)
                return

            player["money"] -= price
            yacht["level"] += 1
            yacht["upgrades"] += 1

            upgrade = YACHT_UPGRADES[yacht["level"]]
            yacht["income"] = upgrade["income"]
            yacht["max_stock"] = upgrade["max_stock"]
            yacht["max_cash"] = upgrade["max_cash"]

            save_player(user_id, player)
            update_yacht(user_id, yacht)

            await call.answer("⬆ Яхт-клуб улучшен!", show_alert=True)

            level = yacht["level"]

        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = YACHT_UPGRADES[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ ЯХТ-КЛУБА {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"🎟 Пропуска: {next_upgrade['max_stock']}\n"
                f"💰 Касса: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )

        await call.message.edit_text(text, reply_markup=yacht_upgrades_kb(user_id, yacht))