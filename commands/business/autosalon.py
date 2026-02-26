import json
import os
import time
import asyncio
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

autosalon_router = Router()

# ======================
# НАСТРОЙКИ
# ======================
AUTOSALON_FILE = "database/autosalon.json"
AUTOSALON_PRICE = 400_000_000
CARS_PRICE = 10_000_000  # цена партии машин

UPGRADES_AUTOSALON = [
    {"level": 0, "income": 800_000, "max_cars": 5, "max_cash": 4_000_000, "price": 0},
    {"level": 1, "income": 1_500_000, "max_cars": 10, "max_cash": 7_050_000, "price": 70_000_000},
    {"level": 2, "income": 1_900_000, "max_cars": 20, "max_cash": 15_000_000, "price": 130_000_000},
    {"level": 3, "income": 2_200_000, "max_cars": 40, "max_cash": 30_000_000, "price": 280_000_000},
]

CYCLE_SECONDS = 3600  # 1 час

# ======================
# БАЗА
# ======================
def load_autosalon():
    if not os.path.exists(AUTOSALON_FILE):
        os.makedirs(os.path.dirname(AUTOSALON_FILE), exist_ok=True)
        with open(AUTOSALON_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(AUTOSALON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_autosalon(data):
    with open(AUTOSALON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_autosalon(user_id):
    data = load_autosalon()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {}
    if "autosalon" not in data[uid]:
        data[uid]["autosalon"] = {
            "owned": False,
            "status": "closed",
            "level": 0,
            "cars": 0,
            "income": 20_000,
            "cycle": CYCLE_SECONDS,
            "last_cycle": 0,
            "cashbox": 0,
            "total_earned": 0,
            "upgrades": 0
        }
        save_autosalon(data)
    level = data[uid]["autosalon"]["level"]
    upgrade = UPGRADES_AUTOSALON[min(level, 3)]
    data[uid]["autosalon"]["income"] = upgrade["income"]
    data[uid]["autosalon"]["max_cars"] = upgrade["max_cars"]
    data[uid]["autosalon"]["max_cash"] = upgrade["max_cash"]
    return data[uid]["autosalon"]

def update_autosalon(user_id, autosalon):
    data = load_autosalon()
    uid = str(user_id)
    data[uid]["autosalon"] = autosalon
    save_autosalon(data)

# ======================
# КНОПКИ
# ======================
def autosalon_main_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶ Открыть салон", callback_data=f"autosalon_open_{user_id}")],
        [InlineKeyboardButton(text="🚗 Закупить машины", callback_data=f"autosalon_buycars_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать выручку", callback_data=f"autosalon_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"autosalon_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"autosalon_upgrades_{user_id}")]
    ])

def autosalon_back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"autosalon_back_{user_id}")]
    ])

def autosalon_upgrades_kb(autosalon, user_id):
    buttons = []
    if autosalon["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"autosalon_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"autosalon_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ======================
# ЦИКЛ ДОХОДА
# ======================
async def autosalon_process_cycle(bot, user_id, autosalon):
    if not autosalon["owned"] or autosalon["status"] != "active":
        return
    now = time.time()
    last = autosalon.get("last_cycle", now)
    cycles = int((now - last) // autosalon["cycle"])
    if cycles <= 0:
        return
    player = get_player(user_id)
    for _ in range(cycles):
        if autosalon["cars"] <= 0:
            autosalon["status"] = "closed"
            await bot.send_message(user_id, "⚠️ Ваш автосалон остановлен: нет машин для продажи!")
            break
        if autosalon["cashbox"] >= autosalon["max_cash"]:
            autosalon["status"] = "closed"
            await bot.send_message(user_id, "💰 Касса автосалона полная, бизнес остановлен!")
            break
        autosalon["cashbox"] += autosalon["income"]
        autosalon["total_earned"] += autosalon["income"]
        autosalon["cars"] -= 1
        if autosalon["cashbox"] > autosalon["max_cash"]:
            autosalon["cashbox"] = autosalon["max_cash"]
    autosalon["last_cycle"] = now
    update_autosalon(user_id, autosalon)

# ======================
# ФОНОВЫЙ ВОРКЕР
# ======================
async def autosalon_background_worker(bot):
    while True:
        data = load_autosalon()
        for user_id in data.keys():
            autosalon = data[user_id].get("autosalon")
            if autosalon:
                await autosalon_process_cycle(bot, int(user_id), autosalon)
        await asyncio.sleep(60)

@autosalon_router.startup()
async def start_autosalon_background(bot):
    asyncio.create_task(autosalon_background_worker(bot))

# ======================
# КОМАНДЫ
# ======================
@autosalon_router.message(F.text.lower() == "купить автосалон")
async def buy_autosalon(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    autosalon = get_autosalon(user_id)
    if autosalon["owned"]:
        await message.answer("⚠️ У вас уже есть автосалон 🚗!")
        return
    if player["money"] < AUTOSALON_PRICE:
        await message.answer("❌ Недостаточно денег")
        return
    player["money"] -= AUTOSALON_PRICE
    player.setdefault("business", []).append("🚗 Автосалон")
    save_player(user_id, player)
    autosalon["owned"] = True
    update_autosalon(user_id, autosalon)
    await message.answer("🚗 Автосалон куплен!: Команда - мой автосалон")

@autosalon_router.message(F.text.lower() == "продать автосалон")
async def sell_autosalon(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    autosalon = get_autosalon(user_id)
    if not autosalon["owned"]:
        await message.answer("⚠️ У вас нет автосалона 🚗!")
        return
    refund = int(AUTOSALON_PRICE * 0.75)
    player["money"] += refund
    if "🚗 Автосалон" in player.get("business", []):
        player["business"].remove("🚗 Автосалон")
    save_player(user_id, player)
    autosalon.update({
        "owned": False,
        "status": "closed",
        "level": 0,
        "cars": 0,
        "cashbox": 0,
        "total_earned": 0,
        "upgrades": 0
    })
    update_autosalon(user_id, autosalon)
    await message.answer(f"🚗 Автосалон продан! Вы получили {refund:,}$")

@autosalon_router.message(lambda m: m.text and m.text.lower() == "мой автосалон")
async def my_autosalon(message: types.Message):
    user_id = message.from_user.id
    autosalon = get_autosalon(user_id)
    if not autosalon["owned"]:
        await message.answer("⚠️ У вас нет автосалона 🚗!")
        return
    status = "🟢 Открыт" if autosalon["status"] == "active" else "🔴 Закрыт"
    remaining = max(0, int(autosalon["cycle"] - (time.time() - autosalon.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)
    text = (
        f"🚗 АВТОСАЛОН\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {autosalon['level']}/3\n\n"
        f"🚙 Машины: {autosalon['cars']} / {autosalon['max_cars']} (Цена партии: {CARS_PRICE:,}$)\n"
        f"💰 В кассе: {autosalon['cashbox']:,}$\n"
        f"💵 Доход: {autosalon['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )
    await message.answer(text, reply_markup=autosalon_main_kb(user_id))

# ======================
# CALLBACKS с защитой
# ======================
async def protect_owner(call: types.CallbackQuery) -> bool:
    if call.data and call.data.split("_")[-1].isdigit():
        owner_id = int(call.data.split("_")[-1])
        if call.from_user.id != owner_id:
            await call.answer("⛓ Это не ваша кнопка.")
            return False
    return True

@autosalon_router.callback_query(F.data.startswith("autosalon_"))
async def autosalon_cb(call: types.CallbackQuery):
    if not await protect_owner(call):
        return
    user_id = call.from_user.id
    autosalon = get_autosalon(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data

    if data.startswith("autosalon_open_"):
        if autosalon["status"] == "active":
            await call.answer("Салон уже открыт!", show_alert=True)
            return
        if autosalon["cars"] <= 0:
            await call.answer("❌ Нет машин для продажи", show_alert=True)
            return
        autosalon["status"] = "active"
        autosalon["last_cycle"] = time.time()
        update_autosalon(user_id, autosalon)
        await call.answer("▶ Салон открыт! Клиенты заходят 😎")
        await refresh_autosalon_menu(call, autosalon)
    elif data.startswith("autosalon_buycars_"):
        if autosalon["cars"] >= autosalon["max_cars"]:
            await call.answer("⚠️ Уже полный склад машин", show_alert=True)
            return
        if player["money"] < CARS_PRICE:
            await call.answer("❌ Недостаточно денег", show_alert=True)
            return
        player["money"] -= CARS_PRICE
        autosalon["cars"] = autosalon["max_cars"]
        save_player(user_id, player)
        update_autosalon(user_id, autosalon)
        await call.answer("🚗 Машины закуплены!", show_alert=True)
        await refresh_autosalon_menu(call, autosalon)
    elif data.startswith("autosalon_take_"):
        if autosalon["cashbox"] <= 0:
            await call.answer("⚠️ Касса пустая!", show_alert=True)
            return
        player["biz_account"] += autosalon["cashbox"]
        autosalon["cashbox"] = 0
        save_player(user_id, player)
        update_autosalon(user_id, autosalon)
        await call.answer(f"+{player['biz_account']:,}$ зачислено на бизнес счёт", show_alert=True)
        await refresh_autosalon_menu(call, autosalon)
    elif data.startswith("autosalon_info_"):
        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = UPGRADES_AUTOSALON[min(autosalon['level'], 3)]
        text = (
            "📊 СТАТУС АВТОСАЛОНА\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"🚗 Тип: Автосалон\n"
            f"📈 Уровень: {autosalon['level']}/3\n"
            f"🚙 Машины: {autosalon['cars']} / {upgrade['max_cars']}\n"
            f"💰 В кассе: {autosalon['cashbox']:,}$\n"
            f"💵 Доход: {upgrade['income']:,}$ / 1h\n\n"
            f"📊 Всего заработано: {autosalon['total_earned']:,}$\n"
            f"⬆ Улучшений: {autosalon['upgrades']}/3"
        )
        await call.message.edit_text(text, reply_markup=autosalon_back_kb(user_id), parse_mode="HTML")
    elif data.startswith("autosalon_back_"):
        await refresh_autosalon_menu(call, autosalon)
    elif data.startswith("autosalon_upgrades_") or data.startswith("autosalon_upgrade_"):
        level = autosalon["level"]
        if data.startswith("autosalon_upgrade_"):
            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return
            price = UPGRADES_AUTOSALON[level + 1]["price"]
            if player["money"] < price:
                await call.answer("❌ Недостаточно денег", show_alert=True)
                return
            player["money"] -= price
            autosalon["level"] += 1
            autosalon["upgrades"] += 1
            upgrade = UPGRADES_AUTOSALON[autosalon["level"]]
            autosalon["income"] = upgrade["income"]
            autosalon["max_cars"] = upgrade["max_cars"]
            autosalon["max_cash"] = upgrade["max_cash"]
            save_player(user_id, player)
            update_autosalon(user_id, autosalon)
            await call.answer("⬆ Автосалон улучшен!", show_alert=True)
            level = autosalon["level"]
        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = UPGRADES_AUTOSALON[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ АВТОСАЛОНА {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"🚙 Склад: {next_upgrade['max_cars']}\n"
                f"💰 Касса: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )
        await call.message.edit_text(text, reply_markup=autosalon_upgrades_kb(autosalon,user_id))

# ======================
# ОБНОВЛЕНИЕ МЕНЮ
# ======================
async def refresh_autosalon_menu(call: types.CallbackQuery, autosalon):
    user_id = call.from_user.id
    status = "🟢 Открыт" if autosalon["status"] == "active" else "🔴 Закрыт"
    remaining = max(0, int(autosalon["cycle"] - (time.time() - autosalon.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)
    text = (
        f"🚗 АВТОСАЛОН\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {autosalon['level']}/3\n\n"
        f"🚙 Машины: {autosalon['cars']} / {autosalon['max_cars']} (Цена партии: {CARS_PRICE:,}$)\n"
        f"💰 В кассе: {autosalon['cashbox']:,}$\n"
        f"💵 Доход: {autosalon['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )
    await call.message.edit_text(text, reply_markup=autosalon_main_kb(user_id))