# Файл: commands/business/vapeshop.py

import json
import os
import time
import asyncio
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

router = Router()

BIZ_FILE = "database/business.json"
VAPE_PRICE = 8_000_000
STOCK_PRICE = 250_000
CYCLE_SECONDS = 3600  # 10 минут

UPGRADES = [
    {"level": 0, "income": 25_000, "max_stock": 120, "max_cash": 60_000, "price": 0},
    {"level": 1, "income": 50_000, "max_stock": 220, "max_cash": 140_000, "price": 3_000_000},
    {"level": 2, "income": 85_000, "max_stock": 360, "max_cash": 300_000, "price": 7_000_000},
    {"level": 3, "income": 120_000, "max_stock": 600, "max_cash": 700_000, "price": 14_000_000},
]

# ======================
# БАЗА
# ======================

def load_biz():
    if not os.path.exists(BIZ_FILE):
        os.makedirs(os.path.dirname(BIZ_FILE), exist_ok=True)
        with open(BIZ_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(BIZ_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_biz(data):
    with open(BIZ_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_vape(user_id):
    data = load_biz()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {}

    if "vape" not in data[uid]:
        data[uid]["vape"] = {
            "owned": False,
            "status": "stopped",
            "level": 0,
            "stock": 0,
            "income": 25_000,
            "cycle": CYCLE_SECONDS,
            "last_cycle": 0,
            "cashbox": 0,
            "total_earned": 0,
            "upgrades": 0
        }
        save_biz(data)

    level = data[uid]["vape"]["level"]
    upgrade = UPGRADES[min(level, 3)]

    data[uid]["vape"]["income"] = upgrade["income"]
    data[uid]["vape"]["max_stock"] = upgrade["max_stock"]
    data[uid]["vape"]["max_cash"] = upgrade["max_cash"]

    return data[uid]["vape"]

def update_vape(user_id, vape):
    data = load_biz()
    uid = str(user_id)
    data[uid]["vape"] = vape
    save_biz(data)

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
        [InlineKeyboardButton(text="▶ Открыть магазин", callback_data=f"vape_open_{user_id}")],
        [InlineKeyboardButton(text="🧪 Закупить жидкости", callback_data=f"vape_buy_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать выручку", callback_data=f"vape_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"vape_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"vape_upgrades_{user_id}")]
    ])

def back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"vape_back_{user_id}")]
    ])

def upgrades_kb(user_id, vape):
    buttons = []
    if vape["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"vape_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"vape_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ======================
# ЦИКЛ ПРОДАЖ (фоновый)
# ======================

async def vape_process_cycle(bot, user_id, vape):
    if vape["status"] != "working":
        return

    now = time.time()
    last = vape.get("last_cycle", now)
    cycles = int((now - last) // vape["cycle"])

    if cycles <= 0:
        return

    for _ in range(cycles):

        if vape["stock"] <= 0:
            vape["status"] = "stopped"
            await bot.send_message(user_id, "⚠️ Магазин остановлен: закончились жидкости!")
            break

        if vape["cashbox"] >= vape["max_cash"]:
            vape["status"] = "stopped"
            await bot.send_message(user_id, "💰 Касса заполнена, работа приостановлена!")
            break

        vape["stock"] -= 1
        vape["cashbox"] += vape["income"]
        vape["total_earned"] += vape["income"]

        if vape["cashbox"] > vape["max_cash"]:
            vape["cashbox"] = vape["max_cash"]

    vape["last_cycle"] = now
    update_vape(user_id, vape)

async def vape_background_worker(bot):
    while True:
        data = load_biz()
        for user_id in data.keys():
            vape = data[user_id].get("vape")
            if vape:
                await vape_process_cycle(bot, int(user_id), vape)
        await asyncio.sleep(60)

@router.startup()
async def start_vape_background(bot):
    asyncio.create_task(vape_background_worker(bot))

# ======================
# ОБНОВЛЕНИЕ МЕНЮ
# ======================

async def refresh_vape_menu(call: types.CallbackQuery, vape):
    user_id = call.from_user.id

    status = "🟢 Открыт" if vape["status"] == "working" else "🔴 Закрыт"
    remaining = max(0, int(vape["cycle"] - (time.time() - vape.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"💨 ВЕЙП-ШОП «ПАРОХОД»\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {vape['level']}/3\n\n"
        f"🧪 Товар: {vape['stock']} / {vape['max_stock']} (Цена партии: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {vape['cashbox']:,}$\n"
        f"💵 Доход: {vape['income']:,}$ / 1h\n"
        f"⏱ Цикл продаж: 1h\n"
        f"⏳ До следующего запуска: {minutes:02d}:{seconds:02d}"
    )

    await call.message.edit_text(text, reply_markup=main_kb(user_id))

# ======================
# КОМАНДЫ
# ======================

@router.message(F.text.lower() == "купить вейпшоп")
async def buy_vape(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    vape = get_vape(user_id)

    if vape["owned"]:
        await message.answer("⚠️ У вас уже есть вейпшоп!")
        return

    if player["money"] < VAPE_PRICE:
        await message.answer("🤡 Недостаточно денег")
        return

    player["money"] -= VAPE_PRICE
    player.setdefault("business", []).append("💨 Вейпшоп")
    save_player(user_id, player)

    vape["owned"] = True
    update_vape(user_id, vape)

    await message.answer("💨🧾 Вейпшоп куплен!: Команда - Мой вейпшоп")

@router.message(F.text.lower() == "продать вейпшоп")
async def sell_vape(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    vape = get_vape(user_id)

    if not vape["owned"]:
        await message.answer("⚠️ У вас нет вейпшопа!")
        return

    refund = int(VAPE_PRICE * 0.75)
    player["money"] += refund

    if "💨 Вейпшоп" in player.get("business", []):
        player["business"].remove("💨 Вейпшоп")

    save_player(user_id, player)

    vape.update({
        "owned": False,
        "status": "stopped",
        "level": 0,
        "stock": 0,
        "cashbox": 0,
        "total_earned": 0,
        "upgrades": 0
    })

    update_vape(user_id, vape)

    await message.answer(f"💨🧾 Вейпшоп продан! Вы получили {refund:,}$")

@router.message(F.text.lower() == "мой вейпшоп")
async def my_vape(message: types.Message):
    user_id = message.from_user.id
    vape = get_vape(user_id)

    if not vape["owned"]:
        await message.answer("⚠️ У вас нет вейпшопа!")
        return

    await vape_process_cycle(message.bot, user_id, vape)

    status = "🟢 Открыт" if vape["status"] == "working" else "🔴 Закрыт"
    remaining = max(0, int(vape["cycle"] - (time.time() - vape.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"💨 ВЕЙП-ШОП «ПАРОХОД»\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {vape['level']}/3\n\n"
        f"🧪 Товар: {vape['stock']} / {vape['max_stock']} (Цена партии: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {vape['cashbox']:,}$\n"
        f"💵 Доход: {vape['income']:,}$ / 1h\n"
        f"⏱ Цикл продаж: 1h\n"
        f"⏳ До следующего запуска: {minutes:02d}:{seconds:02d}"
    )

    await message.answer(text, reply_markup=main_kb(user_id))

# ======================
# CALLBACKS
# ======================

@router.callback_query(F.data.startswith("vape_"))
async def vape_callbacks(call: types.CallbackQuery):

    if not await protect_owner(call):
        return

    user_id = call.from_user.id
    vape = get_vape(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data

    if data.startswith("vape_open_"):

        if vape["status"] == "working":
            await call.answer("Магазин уже открыт!", show_alert=True)
            return

        if vape["stock"] <= 0:
            await call.answer("❌ Нет жидкостей", show_alert=True)
            return

        vape["status"] = "working"
        vape["last_cycle"] = time.time()
        update_vape(user_id, vape)

        await call.answer("▶ Магазин открыт! Клиенты пошли 😎")
        await refresh_vape_menu(call, vape)

    elif data.startswith("vape_buy_"):

        if vape["stock"] >= vape["max_stock"]:
            await call.answer("⚠️ Уже полный склад", show_alert=True)
            return

        if player["money"] < STOCK_PRICE:
            await call.answer("🤡 Недостаточно средств", show_alert=True)
            return

        player["money"] -= STOCK_PRICE
        vape["stock"] = vape["max_stock"]

        save_player(user_id, player)
        update_vape(user_id, vape)

        await call.answer("🧪 Жидкости закуплены!", show_alert=True)
        await refresh_vape_menu(call, vape)

    elif data.startswith("vape_take_"):

        if vape["cashbox"] <= 0:
            await call.answer("⚠️ Касса пуста!", show_alert=True)
            return

        player.setdefault("biz_account", 0)
        player["biz_account"] += vape["cashbox"]
        vape["cashbox"] = 0

        save_player(user_id, player)
        update_vape(user_id, vape)

        await call.answer("💰 Деньги зачислены на бизнес счёт", show_alert=True)
        await refresh_vape_menu(call, vape)

    elif data.startswith("vape_info_"):

        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = UPGRADES[min(vape['level'], 3)]

        text = (
            "📊 СТАТУС ВЕЙП-ШОПА\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"🏪 Тип: Вейп-шоп\n"
            f"📈 Уровень: {vape['level']}/3\n"
            f"🧪 Товар: {vape['stock']} / {upgrade['max_stock']}\n"
            f"💰 В кассе: {vape['cashbox']:,}$\n"
            f"💵 Доход: {upgrade['income']:,}$ / 1h\n\n"
            f"📊 Всего заработано: {vape['total_earned']:,}$\n"
            f"⬆ Улучшений: {vape['upgrades']}/3"
        )

        await call.message.edit_text(text, reply_markup=back_kb(user_id))

    elif data.startswith("vape_back_"):
        await refresh_vape_menu(call, vape)

    elif data.startswith("vape_upgrades_") or data.startswith("vape_upgrade_"):

        level = vape["level"]

        if data.startswith("vape_upgrade_"):

            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return

            price = UPGRADES[level + 1]["price"]

            if player["money"] < price:
                await call.answer("🤡 Недостаточно денег", show_alert=True)
                return

            player["money"] -= price
            vape["level"] += 1
            vape["upgrades"] += 1

            upgrade = UPGRADES[vape["level"]]
            vape["income"] = upgrade["income"]
            vape["max_stock"] = upgrade["max_stock"]
            vape["max_cash"] = upgrade["max_cash"]

            save_player(user_id, player)
            update_vape(user_id, vape)

            await call.answer("⬆ Магазин улучшен!", show_alert=True)

            level = vape["level"]

        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = UPGRADES[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ «ПАРОХОД» {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"📦 Склад: {next_upgrade['max_stock']}\n"
                f"💰 Касса: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )

        await call.message.edit_text(text, reply_markup=upgrades_kb(user_id, vape))