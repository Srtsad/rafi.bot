import json
import os
import time
import asyncio
from random import randint
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

drug_router = Router()

# ======================
# НАСТРОЙКИ
# ======================
DC_FILE = "database/drug_control.json"
DC_PRICE = 20_000_000_000
STOCK_PRICE = 200_000_000  # материалы для операций

DC_UPGRADES = [
    {"level": 0, "income": 150_000_000, "max_stock": 5, "max_cash": 800_000, "price": 0},
    {"level": 1, "income": 200_000_000, "max_stock": 10, "max_cash": 2_000_000_000, "price": 6_000_000_000},
    {"level": 2, "income": 290_000_000, "max_stock": 20, "max_cash": 4_000_000_000, "price": 12_000_000_000},
    {"level": 3, "income": 600_000_000, "max_stock": 50, "max_cash": 9_000_000_000, "price": 20_000_000_000},
]

CYCLE_SECONDS = 3600  # 10 минут

# ======================
# БАЗА
# ======================
def load_dc():
    if not os.path.exists(DC_FILE):
        os.makedirs(os.path.dirname(DC_FILE), exist_ok=True)
        with open(DC_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(DC_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_dc(data):
    with open(DC_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_dc(user_id):
    data = load_dc()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {}
    if "dc" not in data[uid]:
        data[uid]["dc"] = {
            "owned": False,
            "status": "stopped",
            "level": 0,
            "stock": 0,
            "income": 80_000,
            "cycle": CYCLE_SECONDS,
            "last_cycle": 0,
            "cashbox": 0,
            "total_earned": 0,
            "upgrades": 0
        }
        save_dc(data)
    level = data[uid]["dc"]["level"]
    upgrade = DC_UPGRADES[min(level, 3)]
    data[uid]["dc"]["income"] = upgrade["income"]
    data[uid]["dc"]["max_stock"] = upgrade["max_stock"]
    data[uid]["dc"]["max_cash"] = upgrade["max_cash"]
    return data[uid]["dc"]

def update_dc(user_id, dc):
    data = load_dc()
    uid = str(user_id)
    data[uid]["dc"] = dc
    save_dc(data)

# ======================
# КНОПКИ
# ======================
def dc_main_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚨 Начать контроль", callback_data=f"dc_open_{user_id}")],
        [InlineKeyboardButton(text="⚡ Закупить материалы", callback_data=f"dc_buy_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать доход", callback_data=f"dc_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"dc_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"dc_upgrades_{user_id}")]
    ])

def dc_back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"dc_back_{user_id}")]
    ])

def dc_upgrades_kb(dc, user_id):
    buttons = []
    if dc["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"dc_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"dc_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ======================
# ЦИКЛ ДОХОДА
# ======================
async def dc_process_cycle(bot, user_id, dc):
    if dc["status"] != "active":
        return
    now = time.time()
    last = dc.get("last_cycle", now)
    cycles = int((now - last) // dc["cycle"])
    if cycles <= 0:
        return
    player = get_player(user_id)
    for _ in range(cycles):
        if dc["stock"] <= 0:
            dc["status"] = "stopped"
            await bot.send_message(user_id, "⚠️ Наркоконтроль остановлен: нет материалов!")
            break
        if dc["cashbox"] >= dc["max_cash"]:
            dc["status"] = "stopped"
            await bot.send_message(user_id, "💰 Касса Наркоконтроля полна, доход остановлен!")
            break
        gain = randint(0, dc["income"] * 2)
        dc["cashbox"] += gain
        dc["total_earned"] += gain
        dc["stock"] -= 1
        if dc["cashbox"] > dc["max_cash"]:
            dc["cashbox"] = dc["max_cash"]
    dc["last_cycle"] = now
    update_dc(user_id, dc)

# ======================
# ФОНОВЫЙ ВОРКЕР
# ======================
async def dc_background_worker(bot):
    while True:
        data = load_dc()
        for user_id in data.keys():
            dc = data[user_id].get("dc")
            if dc:
                await dc_process_cycle(bot, int(user_id), dc)
        await asyncio.sleep(60)

@drug_router.startup()
async def start_dc_background(bot):
    asyncio.create_task(dc_background_worker(bot))

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
# ОБНОВЛЕНИЕ МЕНЮ
# ======================
async def refresh_dc_menu(call: types.CallbackQuery, dc):
    user_id = call.from_user.id
    status = "🟢 Активен" if dc["status"] == "active" else "🔴 Закрыт"
    remaining = max(0, int(dc.get("cycle", 600) - (time.time() - dc.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)
    text = (
        f"🚨 НАРКОКОНТРОЛЬ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {dc['level']}/3\n\n"
        f"⚡ Материалы: {dc['stock']} / {dc['max_stock']} (Цена: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {dc['cashbox']:,}$\n"
        f"💵 Доход: {dc['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )
    await call.message.edit_text(text, reply_markup=dc_main_kb(user_id))


# ======================
# КОМАНДЫ
# ======================
@drug_router.message(F.text.lower() == "купить контроль")
async def buy_dc(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    dc = get_dc(user_id)
    if dc["owned"]:
        await message.answer("⚠️ У вас уже есть Наркоконтроль 🚨!")
        return
    if player["money"] < DC_PRICE:
        await message.answer("❌ Недостаточно денег")
        return
    player["money"] -= DC_PRICE
    player.setdefault("business", []).append("🚨 Наркоконтроль")
    save_player(user_id, player)
    dc["owned"] = True
    update_dc(user_id, dc)
    await message.answer("🚨 Наркоконтроль куплен! Используйте команду 'Мой контроль'")


@drug_router.message(F.text.lower() == "продать контроль")
async def sell_dc(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    dc = get_dc(user_id)
    if not dc["owned"]:
        await message.answer("⚠️ У вас нет Наркоконтроля 🚨!")
        return
    refund = int(DC_PRICE * 0.75)
    player["money"] += refund
    if "🚨 Наркоконтроль" in player.get("business", []):
        player["business"].remove("🚨 Наркоконтроль")
    save_player(user_id, player)
    dc.update({
        "owned": False,
        "status": "stopped",
        "level": 0,
        "stock": 0,
        "cashbox": 0,
        "total_earned": 0,
        "upgrades": 0
    })
    update_dc(user_id, dc)
    await message.answer(f"🚨 Наркоконтроль продан! Вы получили {refund:,}$")


@drug_router.message(F.text.lower() == "мой контроль")
async def my_dc(message: types.Message):
    user_id = message.from_user.id
    dc = get_dc(user_id)
    if not dc["owned"]:
        await message.answer("⚠️ У вас нет Наркоконтроля 🚨!")
        return
    status = "🟢 Активен" if dc["status"] == "active" else "🔴 Закрыт"
    remaining = max(0, int(dc["cycle"] - (time.time() - dc.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)
    text = (
        f"🚨 НАРКОКОНТРОЛЬ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {dc['level']}/3\n\n"
        f"⚡ Материалы: {dc['stock']} / {dc['max_stock']} (Цена: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {dc['cashbox']:,}$\n"
        f"💵 Доход: {dc['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )
    await message.answer(text, reply_markup=dc_main_kb(user_id))


# ======================
# CALLBACKS
# ======================
@drug_router.callback_query(F.data.startswith("dc_"))
async def dc_cb(call: types.CallbackQuery):
    if not await protect_owner(call):
        return
    user_id = call.from_user.id
    dc = get_dc(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data

    # --- Открыть контроль ---
    if data.startswith("dc_open_"):
        if dc["status"] == "active":
            await call.answer("Наркоконтроль уже активен!", show_alert=True)
            return
        if dc["stock"] <= 0:
            await call.answer("❌ Нет материалов", show_alert=True)
            return
        dc["status"] = "active"
        dc["last_cycle"] = time.time()
        update_dc(user_id, dc)
        await call.answer("🚨 Наркоконтроль запущен! Доход генерируется ⚡")
        await refresh_dc_menu(call, dc)

    # --- Купить материалы ---
    elif data.startswith("dc_buy_"):
        if dc["stock"] >= dc["max_stock"]:
            await call.answer("⚠️ Склад полон", show_alert=True)
            return
        if player["money"] < STOCK_PRICE:
            await call.answer("❌ Недостаточно денег", show_alert=True)
            return
        player["money"] -= STOCK_PRICE
        dc["stock"] = dc["max_stock"]
        save_player(user_id, player)
        update_dc(user_id, dc)
        await call.answer("⚡ Материалы закуплены!", show_alert=True)
        await refresh_dc_menu(call, dc)

    # --- Забрать доход ---
    elif data.startswith("dc_take_"):
        if dc["cashbox"] <= 0:
            await call.answer("⚠️ Касса пуста!", show_alert=True)
            return
        player["biz_account"] += dc["cashbox"]
        dc["cashbox"] = 0
        save_player(user_id, player)
        update_dc(user_id, dc)
        await call.answer(f"+{player['biz_account']:,}$ зачислено на бизнес счёт", show_alert=True)
        await refresh_dc_menu(call, dc)

    # --- Информация ---
    elif data.startswith("dc_info_"):
        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = DC_UPGRADES[min(dc['level'], 3)]
        text = (
            "📊 СТАТУС НАРКОКОНТРОЛЯ\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"🚨 Тип: Наркоконтроль\n"
            f"📈 Уровень: {dc['level']}/3\n"
            f"⚡ Материалы: {dc['stock']} / {upgrade['max_stock']}\n"
            f"💰 В кассе: {dc['cashbox']:,}$\n"
            f"💵 Доход: {upgrade['income']:,}$ / 1h\n\n"
            f"📊 Всего заработано: {dc['total_earned']:,}$\n"
            f"⬆ Улучшений: {dc['upgrades']}/3"
        )
        await call.message.edit_text(text, reply_markup=dc_back_kb(user_id))

    # --- Назад в главное меню ---
    elif data.startswith("dc_back_"):
        await refresh_dc_menu(call, dc)

    # --- Улучшения ---
    elif data.startswith("dc_upgrades_") or data.startswith("dc_upgrade_"):
        level = dc["level"]
        if data.startswith("dc_upgrade_"):
            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return
            price = DC_UPGRADES[level + 1]["price"]
            if player["money"] < price:
                await call.answer("❌ Недостаточно денег", show_alert=True)
                return
            player["money"] -= price
            dc["level"] += 1
            dc["upgrades"] += 1
            upgrade = DC_UPGRADES[dc["level"]]
            dc["income"] = upgrade["income"]
            dc["max_stock"] = upgrade["max_stock"]
            dc["max_cash"] = upgrade["max_cash"]
            save_player(user_id, player)
            update_dc(user_id, dc)
            await call.answer("⬆ Наркоконтроль улучшен!", show_alert=True)
            level = dc["level"]

        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = DC_UPGRADES[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ НАРКОКОНТРОЛЯ {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"⚡ Материалы: {next_upgrade['max_stock']}\n"
                f"💰 Максимальная касса: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )
        await call.message.edit_text(text, reply_markup=dc_upgrades_kb(dc, user_id))