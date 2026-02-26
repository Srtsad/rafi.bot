# Файл: commands/business/stripclub.py

import json
import os
import time
import asyncio
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

stripclub_router = Router()

STRIP_FILE = "database/stripclub.json"
STRIP_PRICE = 100_000_000
STAFF_PRICE = 700_000
CYCLE_SECONDS = 3600  # 10 минут

UPGRADES_STRIP = [
    {"level": 0, "income": 400_000, "max_staff": 5, "max_cash": 120_000, "price": 0},
    {"level": 1, "income": 600_000, "max_staff": 12, "max_cash": 300_000, "price": 50_000_000},
    {"level": 2, "income": 800_000, "max_staff": 25, "max_cash": 600_000, "price": 100_000_000},
    {"level": 3, "income": 1_200_000, "max_staff": 40, "max_cash": 1_200_000, "price": 200_000_000},
]

# ======================
# БАЗА
# ======================

def load_strip():
    if not os.path.exists(STRIP_FILE):
        os.makedirs(os.path.dirname(STRIP_FILE), exist_ok=True)
        with open(STRIP_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(STRIP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_strip(data):
    with open(STRIP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_strip(user_id):
    data = load_strip()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {}

    if "strip" not in data[uid]:
        data[uid]["strip"] = {
            "owned": False,
            "status": "closed",
            "level": 0,
            "staff": 0,
            "income": 400_000,
            "cycle": CYCLE_SECONDS,
            "last_cycle": 0,
            "cashbox": 0,
            "total_earned": 0,
            "upgrades": 0
        }
        save_strip(data)

    level = data[uid]["strip"]["level"]
    upgrade = UPGRADES_STRIP[min(level, 3)]

    data[uid]["strip"]["income"] = upgrade["income"]
    data[uid]["strip"]["max_staff"] = upgrade["max_staff"]
    data[uid]["strip"]["max_cash"] = upgrade["max_cash"]

    return data[uid]["strip"]

def update_strip(user_id, strip):
    data = load_strip()
    uid = str(user_id)
    data[uid]["strip"] = strip
    save_strip(data)

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

def strip_main_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶ Открыть клуб", callback_data=f"strip_open_{user_id}")],
        [InlineKeyboardButton(text="👥 Нанять персонал", callback_data=f"strip_hire_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать выручку", callback_data=f"strip_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"strip_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"strip_upgrades_{user_id}")]
    ])

def strip_back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"strip_back_{user_id}")]
    ])

def strip_upgrades_kb(user_id, strip):
    buttons = []
    if strip["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"strip_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"strip_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ======================
# ЦИКЛ ДОХОДА (как в магазине)
# ======================

async def strip_process_cycle(bot, user_id, strip):
    if strip["status"] != "open":
        return

    now = time.time()
    last = strip.get("last_cycle", now)
    cycles = int((now - last) // strip["cycle"])

    if cycles <= 0:
        return

    for _ in range(cycles):

        if strip["staff"] <= 0:
            strip["status"] = "closed"
            await bot.send_message(user_id, "⚠️ Клуб остановлен: нет персонала!")
            break

        if strip["cashbox"] >= strip["max_cash"]:
            strip["status"] = "closed"
            await bot.send_message(user_id, "💰 Касса заполнена, работа приостановлена!")
            break

        strip["staff"] -= 1
        strip["cashbox"] += strip["income"]
        strip["total_earned"] += strip["income"]

        if strip["cashbox"] > strip["max_cash"]:
            strip["cashbox"] = strip["max_cash"]

    strip["last_cycle"] = now
    update_strip(user_id, strip)

# ======================
# ФОНОВЫЙ ВОРКЕР
# ======================

async def strip_background_worker(bot):
    while True:
        data = load_strip()
        for user_id in data.keys():
            strip = data[user_id].get("strip")
            if strip:
                await strip_process_cycle(bot, int(user_id), strip)
        await asyncio.sleep(60)

@stripclub_router.startup()
async def start_strip_background(bot):
    asyncio.create_task(strip_background_worker(bot))

# ======================
# ОБНОВЛЕНИЕ МЕНЮ
# ======================

async def refresh_strip_menu(call: types.CallbackQuery, strip):
    user_id = call.from_user.id

    status = "🟢 Открыт" if strip["status"] == "open" else "🔴 Закрыт"
    remaining = max(0, int(strip["cycle"] - (time.time() - strip.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"💃 СТРИП КЛУБ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {strip['level']}/3\n\n"
        f"👥 Персонал: {strip['staff']} / {strip['max_staff']} (Цена найма: {STAFF_PRICE:,}$)\n"
        f"💰 В кассе: {strip['cashbox']:,}$\n"
        f"💵 Доход: {strip['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await call.message.edit_text(text, reply_markup=strip_main_kb(user_id))

# ======================
# КОМАНДЫ
# ======================

@stripclub_router.message(F.text.lower() == "купить стрип клуб")
async def buy_strip(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    strip = get_strip(user_id)

    if strip["owned"]:
        await message.answer("⚠️ У вас уже есть стрип клуб!")
        return

    if player["money"] < STRIP_PRICE:
        await message.answer("❌ Недостаточно денег")
        return

    player["money"] -= STRIP_PRICE
    player.setdefault("business", []).append("💃 Стрип клуб")
    save_player(user_id, player)

    strip["owned"] = True
    update_strip(user_id, strip)

    await message.answer("💃 Стрип клуб куплен!: Команда - Мой стрип клуб")

@stripclub_router.message(F.text.lower() == "продать стрип клуб")
async def sell_strip(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    strip = get_strip(user_id)

    if not strip["owned"]:
        await message.answer("⚠️ У вас нет стрип клуба!")
        return

    refund = int(STRIP_PRICE * 0.75)
    player["money"] += refund

    if "💃 Стрип клуб" in player.get("business", []):
        player["business"].remove("💃 Стрип клуб")

    save_player(user_id, player)

    strip.update({
        "owned": False,
        "status": "closed",
        "level": 0,
        "staff": 0,
        "cashbox": 0,
        "total_earned": 0,
        "upgrades": 0
    })

    update_strip(user_id, strip)

    await message.answer(f"💃 Стрип клуб продан! Вы получили {refund:,}$")

@stripclub_router.message(F.text.lower() == "мой стрип клуб")
async def my_strip(message: types.Message):
    user_id = message.from_user.id
    strip = get_strip(user_id)

    if not strip["owned"]:
        await message.answer("⚠️ У вас нет стрип клуба!")
        return

    await strip_process_cycle(message.bot, user_id, strip)

    status = "🟢 Открыт" if strip["status"] == "open" else "🔴 Закрыт"
    remaining = max(0, int(strip["cycle"] - (time.time() - strip.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"💃 СТРИП КЛУБ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {strip['level']}/3\n\n"
        f"👥 Персонал: {strip['staff']} / {strip['max_staff']} (Цена найма: {STAFF_PRICE:,}$)\n"
        f"💰 В кассе: {strip['cashbox']:,}$\n"
        f"💵 Доход: {strip['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )

    await message.answer(text, reply_markup=strip_main_kb(user_id))

# ======================
# CALLBACKS
# ======================

@stripclub_router.callback_query(F.data.startswith("strip_"))
async def strip_callbacks(call: types.CallbackQuery):

    if not await protect_owner(call):
        return

    user_id = call.from_user.id
    strip = get_strip(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data

    if data.startswith("strip_open_"):

        if strip["status"] == "open":
            await call.answer("Клуб уже открыт!", show_alert=True)
            return

        if strip["staff"] <= 0:
            await call.answer("❌ Нет персонала", show_alert=True)
            return

        strip["status"] = "open"
        strip["last_cycle"] = time.time()
        update_strip(user_id, strip)

        await call.answer("▶ Клуб открыт! Доход пошёл 😎")
        await refresh_strip_menu(call, strip)

    elif data.startswith("strip_hire_"):

        if strip["staff"] >= strip["max_staff"]:
            await call.answer("⚠️ Максимальный персонал", show_alert=True)
            return

        if player["money"] < STAFF_PRICE:
            await call.answer("❌ Недостаточно денег", show_alert=True)
            return

        player["money"] -= STAFF_PRICE
        strip["staff"] = strip["max_staff"]

        save_player(user_id, player)
        update_strip(user_id, strip)

        await call.answer("👥 Персонал нанят!", show_alert=True)
        await refresh_strip_menu(call, strip)

    elif data.startswith("strip_take_"):

        if strip["cashbox"] <= 0:
            await call.answer("⚠️ Касса пуста!", show_alert=True)
            return

        player.setdefault("biz_account", 0)
        player["biz_account"] += strip["cashbox"]
        strip["cashbox"] = 0

        save_player(user_id, player)
        update_strip(user_id, strip)

        await call.answer("💰 Деньги зачислены на бизнес счёт", show_alert=True)
        await refresh_strip_menu(call, strip)

    elif data.startswith("strip_info_"):

        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = UPGRADES_STRIP[min(strip['level'], 3)]

        text = (
            "📊 СТАТУС СТРИП КЛУБА\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"💃 Тип: Стрип клуб\n"
            f"📈 Уровень: {strip['level']}/3\n"
            f"👥 Персонал: {strip['staff']} / {upgrade['max_staff']}\n"
            f"💰 В кассе: {strip['cashbox']:,}$\n"
            f"💵 Доход: {upgrade['income']:,}$ / 1h\n\n"
            f"📊 Всего заработано: {strip['total_earned']:,}$\n"
            f"⬆ Улучшений: {strip['upgrades']}/3"
        )

        await call.message.edit_text(text, reply_markup=strip_back_kb(user_id))

    elif data.startswith("strip_back_"):
        await refresh_strip_menu(call, strip)

    elif data.startswith("strip_upgrades_") or data.startswith("strip_upgrade_"):

        level = strip["level"]

        if data.startswith("strip_upgrade_"):

            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return

            price = UPGRADES_STRIP[level + 1]["price"]

            if player["money"] < price:
                await call.answer("❌ Недостаточно денег", show_alert=True)
                return

            player["money"] -= price
            strip["level"] += 1
            strip["upgrades"] += 1

            upgrade = UPGRADES_STRIP[strip["level"]]
            strip["income"] = upgrade["income"]
            strip["max_staff"] = upgrade["max_staff"]
            strip["max_cash"] = upgrade["max_cash"]

            save_player(user_id, player)
            update_strip(user_id, strip)

            await call.answer("⬆ Клуб улучшен!", show_alert=True)

            level = strip["level"]

        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = UPGRADES_STRIP[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ СТРИП КЛУБА {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"👥 Персонал: {next_upgrade['max_staff']}\n"
                f"💰 Касса: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )

        await call.message.edit_text(text, reply_markup=strip_upgrades_kb(user_id, strip))