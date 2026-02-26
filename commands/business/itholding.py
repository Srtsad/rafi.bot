# Файл: commands/business/itholding.py

import json
import os
import time
import asyncio
from random import randint
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

itholding_router = Router()

# ======================
# НАСТРОЙКИ
# ======================

ITH_FILE = "database/itholding.json"
ITH_PRICE = 15_000_000_000
STOCK_PRICE = 500_000_000


ITH_UPGRADES = [
    {"level": 0, "income": 150_000_000, "max_stock": 10, "max_cash": 600_000, "price": 0},
    {"level": 1, "income": 180_000_000, "max_stock": 25, "max_cash": 5_400_000_000, "price": 600_000_000},
    {"level": 2, "income": 200_000_000, "max_stock": 50, "max_cash": 7_800_000_000, "price": 900_000_000},
    {"level": 3, "income": 230_000_000, "max_stock": 100, "max_cash": 10_600_000_000, "price": 3_000_000_000},
]

CYCLE_SECONDS = 3600

# ======================
# БАЗА
# ======================

def load_ith():
    if not os.path.exists(ITH_FILE):
        os.makedirs(os.path.dirname(ITH_FILE), exist_ok=True)
        with open(ITH_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(ITH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_ith(data):
    with open(ITH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_ith(user_id):
    data = load_ith()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {}

    if "itholding" not in data[uid]:
        data[uid]["itholding"] = {
            "owned": False,
            "status": "stopped",
            "level": 0,
            "stock": 0,
            "income": 60_000,
            "cycle": CYCLE_SECONDS,
            "last_cycle": 0,
            "cashbox": 0,
            "total_earned": 0,
            "upgrades": 0
        }
        save_ith(data)

    level = data[uid]["itholding"]["level"]
    upgrade = ITH_UPGRADES[min(level, 3)]

    data[uid]["itholding"]["income"] = upgrade["income"]
    data[uid]["itholding"]["max_stock"] = upgrade["max_stock"]
    data[uid]["itholding"]["max_cash"] = upgrade["max_cash"]

    return data[uid]["itholding"]

def update_ith(user_id, itholding):
    data = load_ith()
    uid = str(user_id)
    data[uid]["itholding"] = itholding
    save_ith(data)

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

def ith_main_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💻 Запустить IT-холдинг", callback_data=f"ith_open_{user_id}")],
        [InlineKeyboardButton(text="🛒 Закупить ресурсы", callback_data=f"ith_buy_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать доход", callback_data=f"ith_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"ith_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"ith_upgrades_{user_id}")]
    ])

def ith_back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"ith_back_{user_id}")]
    ])

def ith_upgrades_kb(user_id, itholding):
    buttons = []
    if itholding["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"ith_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"ith_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ======================
# ЦИКЛ ДОХОДА
# ======================

async def ith_process_cycle(bot, user_id, itholding):
    if itholding["status"] != "active":
        return

    now = time.time()
    last = itholding.get("last_cycle", now)
    cycles = int((now - last) // itholding["cycle"])

    if cycles <= 0:
        return

    for _ in range(cycles):

        if itholding["stock"] <= 0:
            itholding["status"] = "stopped"
            await bot.send_message(user_id, "⚠️ IT-холдинг остановлен: нет ресурсов!")
            break

        if itholding["cashbox"] >= itholding["max_cash"]:
            itholding["status"] = "stopped"
            await bot.send_message(user_id, "💰 Касса заполнена, производство остановлено!")
            break

        gain = randint(itholding["income"] // 2, itholding["income"] * 2)

        itholding["cashbox"] += gain
        itholding["total_earned"] += gain
        itholding["stock"] -= 1

        if itholding["cashbox"] > itholding["max_cash"]:
            itholding["cashbox"] = itholding["max_cash"]

    itholding["last_cycle"] = now
    update_ith(user_id, itholding)

# ======================
# ФОНОВЫЙ ВОРКЕР
# ======================

async def ith_background_worker(bot):
    while True:
        data = load_ith()
        for user_id in data.keys():
            itholding = data[user_id].get("itholding")
            if itholding:
                await ith_process_cycle(bot, int(user_id), itholding)
        await asyncio.sleep(60)

@itholding_router.startup()
async def start_ith_background(bot):
    asyncio.create_task(ith_background_worker(bot))

# ======================
# ОБНОВЛЕНИЕ МЕНЮ
# ======================

async def refresh_ith_menu(call: types.CallbackQuery, itholding):
    user_id = call.from_user.id

    status = "🟢 Активен" if itholding["status"] == "active" else "🔴 Остановлен"
    remaining = max(0, int(itholding["cycle"] - (time.time() - itholding.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"💻 IT-ХОЛДИНГ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {itholding['level']}/3\n\n"
        f"🛒 Ресурсы: {itholding['stock']} / {itholding['max_stock']} (Цена: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {itholding['cashbox']:,}$\n"
        f"💵 Доход: {itholding['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await call.message.edit_text(text, reply_markup=ith_main_kb(user_id))

# ======================
# КОМАНДЫ
# ======================

@itholding_router.message(F.text.lower().contains("купить холдинг"))
async def buy_ith(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    itholding = get_ith(user_id)

    if itholding["owned"]:
        await message.answer("⚠️ У вас уже есть IT-холдинг 💻!")
        return

    if player["money"] < ITH_PRICE:
        await message.answer("❌ Недостаточно денег")
        return

    player["money"] -= ITH_PRICE
    player.setdefault("business", []).append("💻 IT-холдинг")
    save_player(user_id, player)

    itholding["owned"] = True
    update_ith(user_id, itholding)

    await message.answer("💻 IT-холдинг куплен! Используйте 'Мой холдинг'")

@itholding_router.message(F.text.lower().contains("продать холдинг"))
async def sell_ith(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    itholding = get_ith(user_id)

    if not itholding["owned"]:
        await message.answer("⚠️ У вас нет IT-холдинга 💻!")
        return

    refund = int(ITH_PRICE * 0.75)
    player["money"] += refund

    if "💻 IT-холдинг" in player.get("business", []):
        player["business"].remove("💻 IT-холдинг")

    save_player(user_id, player)

    itholding.update({
        "owned": False,
        "status": "stopped",
        "level": 0,
        "stock": 0,
        "cashbox": 0,
        "total_earned": 0,
        "upgrades": 0
    })

    update_ith(user_id, itholding)

    await message.answer(f"💻 IT-холдинг продан! Вы получили {refund:,}$")

@itholding_router.message(F.text.lower().contains("мой холдинг"))
async def my_ith(message: types.Message):
    user_id = message.from_user.id
    itholding = get_ith(user_id)

    if not itholding["owned"]:
        await message.answer("⚠️ У вас нет IT-холдинга 💻!")
        return

    status = "🟢 Активен" if itholding["status"] == "active" else "🔴 Остановлен"
    remaining = max(0, int(itholding["cycle"] - (time.time() - itholding.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"💻 IT-ХОЛДИНГ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {itholding['level']}/3\n\n"
        f"🛒 Ресурсы: {itholding['stock']} / {itholding['max_stock']} (Цена: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {itholding['cashbox']:,}$\n"
        f"💵 Доход: {itholding['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await message.answer(text, reply_markup=ith_main_kb(user_id))

# ======================
# CALLBACKS
# ======================

@itholding_router.callback_query(F.data.startswith("ith_"))
async def ith_callbacks(call: types.CallbackQuery):
    if not await protect_owner(call):
        return

    user_id = call.from_user.id
    itholding = get_ith(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data

    if data.startswith("ith_open_"):

        if itholding["status"] == "active":
            await call.answer("IT-холдинг уже активен!", show_alert=True)
            return

        if itholding["stock"] <= 0:
            await call.answer("❌ Нет ресурсов", show_alert=True)
            return

        itholding["status"] = "active"
        itholding["last_cycle"] = time.time()
        update_ith(user_id, itholding)

        await call.answer("💻 IT-холдинг запущен! 🚀")
        await refresh_ith_menu(call, itholding)

    elif data.startswith("ith_buy_"):

        if itholding["stock"] >= itholding["max_stock"]:
            await call.answer("⚠️ Склад полон", show_alert=True)
            return

        if player["money"] < STOCK_PRICE:
            await call.answer("❌ Недостаточно денег", show_alert=True)
            return

        player["money"] -= STOCK_PRICE
        itholding["stock"] = itholding["max_stock"]

        save_player(user_id, player)
        update_ith(user_id, itholding)

        await call.answer("🛒 Ресурсы закуплены!", show_alert=True)
        await refresh_ith_menu(call, itholding)

    elif data.startswith("ith_take_"):

        if itholding["cashbox"] <= 0:
            await call.answer("⚠️ Касса пуста!", show_alert=True)
            return

        player["biz_account"] += itholding["cashbox"]
        itholding["cashbox"] = 0

        save_player(user_id, player)
        update_ith(user_id, itholding)

        await call.answer("💰 Доход зачислен!", show_alert=True)
        await refresh_ith_menu(call, itholding)

    elif data.startswith("ith_info_"):

        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = ITH_UPGRADES[min(itholding['level'], 3)]

        text = (
            "📊 СТАТУС IT-ХОЛДИНГА\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"💻 Тип: IT-холдинг\n"
            f"📈 Уровень: {itholding['level']}/3\n"
            f"🛒 Ресурсы: {itholding['stock']} / {upgrade['max_stock']}\n"
            f"💰 В кассе: {itholding['cashbox']:,}$\n"
            f"💵 Доход: {upgrade['income']:,}$ / 1h\n\n"
            f"📊 Всего заработано: {itholding['total_earned']:,}$\n"
            f"⬆ Улучшений: {itholding['upgrades']}/3"
        )

        await call.message.edit_text(text, reply_markup=ith_back_kb(user_id))

    elif data.startswith("ith_back_"):
        await refresh_ith_menu(call, itholding)

    elif data.startswith("ith_upgrades_") or data.startswith("ith_upgrade_"):

        level = itholding["level"]

        if data.startswith("ith_upgrade_"):

            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return

            price = ITH_UPGRADES[level + 1]["price"]

            if player["money"] < price:
                await call.answer("❌ Недостаточно денег", show_alert=True)
                return

            player["money"] -= price
            itholding["level"] += 1
            itholding["upgrades"] += 1

            upgrade = ITH_UPGRADES[itholding["level"]]
            itholding["income"] = upgrade["income"]
            itholding["max_stock"] = upgrade["max_stock"]
            itholding["max_cash"] = upgrade["max_cash"]

            save_player(user_id, player)
            update_ith(user_id, itholding)

            await call.answer("⬆ IT-холдинг улучшен!", show_alert=True)

            level = itholding["level"]

        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = ITH_UPGRADES[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ IT-ХОЛДИНГА {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"🛒 Склад: {next_upgrade['max_stock']}\n"
                f"💰 Касса: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )

        await call.message.edit_text(text, reply_markup=ith_upgrades_kb(user_id, itholding))