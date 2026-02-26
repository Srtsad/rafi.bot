import json
import os
import time
import asyncio
from random import randint
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

corp_router = Router()

# ======================
# НАСТРОЙКИ
# ======================
CORP_FILE = "database/corporation.json"
CORP_PRICE = 9_000_000_000
STOCK_PRICE = 250_000_000  # цена партии материалов

UPGRADES_CORP = [
    {"level": 0, "income": 90_000_000, "max_stock": 10, "max_cash": 5_000_000_000, "price": 0},
    {"level": 1, "income": 120_000_000, "max_stock": 25, "max_cash": 8_200_000_000, "price": 900_000_000},
    {"level": 2, "income": 150_050_000, "max_stock": 50, "max_cash": 9_500_000_000, "price": 1_000_000_000},
    {"level": 3, "income": 180_000_000, "max_stock": 100, "max_cash": 10_000_000_000, "price": 5_000_000_000},
]

CYCLE_SECONDS = 3600  # 1 час

# ======================
# БАЗА
# ======================
def load_corp():
    if not os.path.exists(CORP_FILE):
        os.makedirs(os.path.dirname(CORP_FILE), exist_ok=True)
        with open(CORP_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(CORP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_corp(data):
    with open(CORP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_corp(user_id):
    data = load_corp()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {}
    if "corp" not in data[uid]:
        data[uid]["corp"] = {
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
        save_corp(data)
    level = data[uid]["corp"]["level"]
    upgrade = UPGRADES_CORP[min(level, 3)]
    data[uid]["corp"]["income"] = upgrade["income"]
    data[uid]["corp"]["max_stock"] = upgrade["max_stock"]
    data[uid]["corp"]["max_cash"] = upgrade["max_cash"]
    return data[uid]["corp"]

def update_corp(user_id, corp):
    data = load_corp()
    uid = str(user_id)
    data[uid]["corp"] = corp
    save_corp(data)

# ======================
# КНОПКИ
# ======================
def corp_main_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶ Открыть корпорацию", callback_data=f"corp_open_{user_id}")],
        [InlineKeyboardButton(text="🏗 Закупить материалы", callback_data=f"corp_buy_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать доход", callback_data=f"corp_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"corp_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"corp_upgrades_{user_id}")]
    ])

def corp_back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"corp_back_{user_id}")]
    ])

def corp_upgrades_kb(corp, user_id):
    buttons = []
    if corp["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"corp_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"corp_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ======================
# ЦИКЛ ДОХОДА
# ======================
async def corp_process_cycle(bot, user_id, corp):
    if corp["status"] != "active":
        return
    now = time.time()
    last = corp.get("last_cycle", now)
    cycles = int((now - last) // corp["cycle"])
    if cycles <= 0:
        return
    player = get_player(user_id)
    for _ in range(cycles):
        if corp["stock"] <= 0:
            corp["status"] = "closed"
            await bot.send_message(user_id, "⚠️ Корпорация остановлена: нет материалов!")
            break
        if corp["cashbox"] >= corp["max_cash"]:
            corp["status"] = "closed"
            await bot.send_message(user_id, "💰 Касса корпорации полна, доход остановлен!")
            break
        gain = randint(0, corp["income"] * 2)
        corp["cashbox"] += gain
        corp["total_earned"] += gain
        corp["stock"] -= 1
        if corp["cashbox"] > corp["max_cash"]:
            corp["cashbox"] = corp["max_cash"]
    corp["last_cycle"] = now
    update_corp(user_id, corp)

# ======================
# ФОНОВЫЙ ВОРКЕР
# ======================
async def corp_background_worker(bot):
    while True:
        data = load_corp()
        for user_id in data.keys():
            corp = data[user_id].get("corp")
            if corp:
                await corp_process_cycle(bot, int(user_id), corp)
        await asyncio.sleep(60)

@corp_router.startup()
async def start_corp_background(bot):
    asyncio.create_task(corp_background_worker(bot))

# ======================
# ЗАЩИТА КНОПОК
# ======================
async def protect_owner(call: types.CallbackQuery) -> bool:
    if call.data and call.data.split("_")[-1].isdigit():
        owner_id = int(call.data.split("_")[-1])
        if call.from_user.id != owner_id:
            await call.answer("⛓ Это не ваша кнопка.")
            return False
    return True

# ======================
# КОМАНДЫ
# ======================
@corp_router.message(F.text.lower() == "купить корпорацию")
async def buy_corp(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    corp = get_corp(user_id)
    if corp["owned"]:
        await message.answer("⚠️ У вас уже есть корпорация 🏢!")
        return
    if player["money"] < CORP_PRICE:
        await message.answer("❌ Недостаточно денег")
        return
    player["money"] -= CORP_PRICE
    player.setdefault("business", []).append("🏢 Корпорация")
    save_player(user_id, player)
    corp["owned"] = True
    update_corp(user_id, corp)
    await message.answer("🏢 Корпорация куплена! Используйте команду 'Моя корпорация'")

@corp_router.message(F.text.lower() == "продать корпорацию")
async def sell_corp(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    corp = get_corp(user_id)
    if not corp["owned"]:
        await message.answer("⚠️ У вас нет корпорации 🏢!")
        return
    refund = int(CORP_PRICE * 0.75)
    player["money"] += refund
    if "🏢 Корпорация" in player.get("business", []):
        player["business"].remove("🏢 Корпорация")
    save_player(user_id, player)
    corp.update({
        "owned": False,
        "status": "closed",
        "level": 0,
        "stock": 0,
        "cashbox": 0,
        "total_earned": 0,
        "upgrades": 0
    })
    update_corp(user_id, corp)
    await message.answer(f"🏢 Корпорация продана! Вы получили {refund:,}$")

@corp_router.message(F.text.lower() == "моя корпорация")
async def my_corp(message: types.Message):
    user_id = message.from_user.id
    corp = get_corp(user_id)
    if not corp["owned"]:
        await message.answer("⚠️ У вас нет корпорации 🏢!")
        return
    status = "🟢 Открыта" if corp["status"] == "active" else "🔴 Закрыта"
    remaining = max(0, int(corp["cycle"] - (time.time() - corp.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)
    text = (
        f"🏢 КОРПОРАЦИЯ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {corp['level']}/3\n\n"
        f"🏗 Материалы: {corp['stock']} / {corp['max_stock']} (Цена партии: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {corp['cashbox']:,}$\n"
        f"💵 Потенциальный доход: {corp['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )
    await message.answer(text, reply_markup=corp_main_kb(user_id))

# ======================
# ОБНОВЛЕНИЕ МЕНЮ
# ======================
async def refresh_corp_menu(call: types.CallbackQuery, corp):
    user_id = call.from_user.id
    status = "🟢 Открыта" if corp["status"] == "active" else "🔴 Закрыта"
    remaining = max(0, int(corp["cycle"] - (time.time() - corp.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)
    text = (
        f"🏢 КОРПОРАЦИЯ\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {corp['level']}/3\n\n"
        f"🏗 Материалы: {corp['stock']} / {corp['max_stock']} (Цена партии: {STOCK_PRICE:,}$)\n"
        f"💰 В кассе: {corp['cashbox']:,}$\n"
        f"💵 Потенциальный доход: {corp['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )
    await call.message.edit_text(text, reply_markup=corp_main_kb(user_id))

# ======================
# CALLBACKS
# ======================
@corp_router.callback_query(F.data.startswith("corp_"))
async def corp_cb(call: types.CallbackQuery):
    if not await protect_owner(call):
        return
    user_id = call.from_user.id
    corp = get_corp(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data
    if data.startswith("corp_open_"):
        if corp["status"] == "active":
            await call.answer("Корпорация уже открыта!", show_alert=True)
            return
        if corp["stock"] <= 0:
            await call.answer("❌ Нет материалов", show_alert=True)
            return
        corp["status"] = "active"
        corp["last_cycle"] = time.time()
        update_corp(user_id, corp)
        await call.answer("▶ Корпорация запущена! Доход генерируется 🏗")
        await refresh_corp_menu(call, corp)
    elif data.startswith("corp_buy_"):
        if corp["stock"] >= corp["max_stock"]:
            await call.answer("⚠️ Склад полон", show_alert=True)
            return
        if player["money"] < STOCK_PRICE:
            await call.answer("❌ Недостаточно денег", show_alert=True)
            return
        player["money"] -= STOCK_PRICE
        corp["stock"] = corp["max_stock"]
        save_player(user_id, player)
        update_corp(user_id, corp)
        await call.answer("🏗 Материалы закуплены!", show_alert=True)
        await refresh_corp_menu(call, corp)
    elif data.startswith("corp_take_"):
        if corp["cashbox"] <= 0:
            await call.answer("⚠️ Касса пуста!", show_alert=True)
            return
        player["biz_account"] += corp["cashbox"]
        corp["cashbox"] = 0
        save_player(user_id, player)
        update_corp(user_id, corp)
        await call.answer(f"+{player['biz_account']:,}$ зачислено на бизнес счёт", show_alert=True)
        await refresh_corp_menu(call, corp)
    elif data.startswith("corp_info_"):
        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = UPGRADES_CORP[min(corp['level'], 3)]
        text = (
            "📊 СТАТУС КОРПОРАЦИИ\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"🏢 Тип: Строительная корпорация\n"
            f"📈 Уровень: {corp['level']}/3\n"
            f"🏗 Материалы: {corp['stock']} / {upgrade['max_stock']}\n"
            f"💰 В кассе: {corp['cashbox']:,}$\n"
            f"💵 Доход: {upgrade['income']:,}$ / 1h\n\n"
            f"📊 Всего заработано: {corp['total_earned']:,}$\n"
            f"⬆ Улучшений: {corp['upgrades']}/3"
        )
        await call.message.edit_text(text, reply_markup=corp_back_kb(user_id), parse_mode="HTML")
    elif data.startswith("corp_back_"):
        await refresh_corp_menu(call, corp)
    elif data.startswith("corp_upgrades_") or data.startswith("corp_upgrade_"):
        level = corp["level"]
        if data.startswith("corp_upgrade_"):
            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return
            price = UPGRADES_CORP[level + 1]["price"]
            if player["money"] < price:
                await call.answer("❌ Недостаточно денег", show_alert=True)
                return
            player["money"] -= price
            corp["level"] += 1
            corp["upgrades"] += 1
            upgrade = UPGRADES_CORP[corp["level"]]
            corp["income"] = upgrade["income"]
            corp["max_stock"] = upgrade["max_stock"]
            corp["max_cash"] = upgrade["max_cash"]
            save_player(user_id, player)
            update_corp(user_id, corp)
            await call.answer("⬆ Корпорация улучшена!", show_alert=True)
            level = corp["level"]
        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = UPGRADES_CORP[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ КОРПОРАЦИИ {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"🏗 Склад: {next_upgrade['max_stock']}\n"
                f"💰 Максимальная касса: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )
        await call.message.edit_text(text, reply_markup=corp_upgrades_kb(corp,user_id))