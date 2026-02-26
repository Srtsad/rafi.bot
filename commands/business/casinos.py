import json
import os
import time
import asyncio
from random import randint
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention

casinos_router = Router()

# ======================
# НАСТРОЙКИ
# ======================
CASINO_FILE = "database/casino.json"
CASINO_PRICE = 400_000_000
TABLE_PRICE = 10_000_000  # цена партии столов/слотов

UPGRADES_CASINO = [
    {"level": 0, "income": 800_000, "max_tables": 5, "max_cash": 4_000_000, "price": 0},
    {"level": 1, "income": 1_500_000, "max_tables": 10, "max_cash": 7_050_000, "price": 70_000_000},
    {"level": 2, "income": 1_900_000, "max_tables": 20, "max_cash": 15_000_000, "price": 130_000_000},
    {"level": 3, "income": 2_200_000, "max_tables": 40, "max_cash": 30_000_000, "price": 280_000_000},
]

CYCLE_SECONDS = 3600  # 1 час

# ======================
# БАЗА
# ======================
def load_casino():
    if not os.path.exists(CASINO_FILE):
        os.makedirs(os.path.dirname(CASINO_FILE), exist_ok=True)
        with open(CASINO_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(CASINO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_casino(data):
    with open(CASINO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_casino(user_id):
    data = load_casino()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {}

    if "casino" not in data[uid]:
        data[uid]["casino"] = {
            "owned": False,
            "status": "closed",
            "level": 0,
            "tables": 0,
            "income": 20_000,
            "cycle": CYCLE_SECONDS,
            "last_cycle": 0,
            "cashbox": 0,
            "total_earned": 0,
            "upgrades": 0
        }
        save_casino(data)

    level = data[uid]["casino"]["level"]
    upgrade = UPGRADES_CASINO[min(level, 3)]
    data[uid]["casino"]["income"] = upgrade["income"]
    data[uid]["casino"]["max_tables"] = upgrade["max_tables"]
    data[uid]["casino"]["max_cash"] = upgrade["max_cash"]

    return data[uid]["casino"]

def update_casino(user_id, casino):
    data = load_casino()
    uid = str(user_id)
    data[uid]["casino"] = casino
    save_casino(data)

# ======================
# КНОПКИ
# ======================
def casino_main_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶ Открыть казино", callback_data=f"casino_open_{user_id}")],
        [InlineKeyboardButton(text="🎰 Закупить столы", callback_data=f"casino_buytables_{user_id}")],
        [InlineKeyboardButton(text="💰 Забрать банк", callback_data=f"casino_take_{user_id}")],
        [InlineKeyboardButton(text="📊 Информация", callback_data=f"casino_info_{user_id}")],
        [InlineKeyboardButton(text="⬆ Улучшения", callback_data=f"casino_upgrades_{user_id}")]
    ])

def casino_back_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"casino_back_{user_id}")]
    ])

def casino_upgrades_kb(casino, user_id):
    buttons = []
    if casino["level"] < 3:
        buttons.append([InlineKeyboardButton(text="⬆ Улучшить", callback_data=f"casino_upgrade_{user_id}")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data=f"casino_back_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ======================
# НОВЫЙ ЦИКЛ ДОХОДА
# ======================
async def casino_process_cycle(bot, user_id, casino):

    if not casino["owned"]:
        return

    if casino["status"] != "active":
        return

    now = time.time()
    last = casino.get("last_cycle", now)
    cycles = int((now - last) // casino["cycle"])

    if cycles <= 0:
        return

    for _ in range(cycles):

        # ❌ если нет столов
        if casino["tables"] <= 0:
            casino["status"] = "closed"
            await bot.send_message(
                user_id,
                "⚠️ Ваш бизнес казино остановлен — закончились столы!"
            )
            break

        # ❌ если касса переполнена
        if casino["cashbox"] >= casino["max_cash"]:
            casino["status"] = "closed"
            await bot.send_message(
                user_id,
                "💰 Касса заполнена! Казино остановлено."
            )
            break

        # 🔻 списываем 1 стол
        casino["tables"] -= 1

        # 💵 прибыль
        profit = randint(
            int(casino["income"] * 0.7),
            int(casino["income"] * 1.3)
        )

        casino["cashbox"] += profit
        casino["total_earned"] += profit

        if casino["cashbox"] > casino["max_cash"]:
            casino["cashbox"] = casino["max_cash"]

    casino["last_cycle"] = now
    update_casino(user_id, casino)
# ======================
# ФОНОВЫЙ ВОРКЕР
# ======================
async def casino_background_worker(bot):
    while True:
        data = load_casino()
        for user_id in data.keys():
            casino = data[user_id].get("casino")
            if casino:
                await casino_process_cycle(bot, int(user_id), casino)
        await asyncio.sleep(60)

@casinos_router.startup()
async def start_casino_background(bot):
    asyncio.create_task(casino_background_worker(bot))

# ======================
# КОМАНДЫ
# ======================
@casinos_router.message(F.text.lower() == "купить казино")
async def buy_casino(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    casino = get_casino(user_id)

    if casino["owned"]:
        await message.answer("⚠️ У вас уже есть казино 🎰!")
        return
    if player["money"] < CASINO_PRICE:
        await message.answer("❌ Недостаточно денег")
        return

    player["money"] -= CASINO_PRICE
    player.setdefault("business", []).append("🎰 Казино")
    save_player(user_id, player)

    casino["owned"] = True
    update_casino(user_id, casino)
    await message.answer("🎰 Казино куплено!: Команда - Моё казино")

@casinos_router.message(F.text.lower() == "продать казино")
async def sell_casino(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    casino = get_casino(user_id)

    if not casino["owned"]:
        await message.answer("⚠️ У вас нет казино 🎰!")
        return

    refund = int(CASINO_PRICE * 0.75)
    player["money"] += refund
    if "🎰 Казино" in player.get("business", []):
        player["business"].remove("🎰 Казино")
    save_player(user_id, player)

    casino.update({
        "owned": False,
        "status": "closed",
        "level": 0,
        "tables": 0,
        "cashbox": 0,
        "total_earned": 0,
        "upgrades": 0
    })
    update_casino(user_id, casino)

    await message.answer(f"🎰 Казино продано! Вы получили {refund:,}$")

# ======================
# ОБНОВЛЕНИЕ МЕНЮ
# ======================
@casinos_router.message(lambda m: m.text and m.text.lower() == "моё казино")
async def my_casino(message: types.Message):
    user_id = message.from_user.id
    casino = get_casino(user_id)

    if not casino["owned"]:
        await message.answer("⚠️ У вас нет казино 🎰!")
        return

    status = "🟢 Открыто" if casino["status"] == "active" else "🔴 Закрыто"
    remaining = max(0, int(casino["cycle"] - (time.time() - casino.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🎰 КАЗИНО\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {casino['level']}/3\n\n"
        f"🎲 Столы: {casino['tables']} / {casino['max_tables']} (Цена партии: {TABLE_PRICE:,}$)\n"
        f"💰 В банке: {casino['cashbox']:,}$\n"
        f"💵 Потенциальный доход: {casino['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )
    await message.answer(text, reply_markup=casino_main_kb(user_id))


# ======================
# Функция обновления меню после действий
# ======================
async def refresh_casino_menu(call: types.CallbackQuery, casino):
    user_id = call.from_user.id
    status = "🟢 Открыто" if casino["status"] == "active" else "🔴 Закрыто"
    remaining = max(0, int(casino["cycle"] - (time.time() - casino.get("last_cycle", 0))))
    minutes, seconds = divmod(remaining, 60)

    text = (
        f"🎰 КАЗИНО\n━━━━━━━━━━━━━━\n"
        f"Статус: {status}\n"
        f"Уровень: {casino['level']}/3\n\n"
        f"🎲 Столы: {casino['tables']} / {casino['max_tables']} (Цена партии: {TABLE_PRICE:,}$)\n"
        f"💰 В банке: {casino['cashbox']:,}$\n"
        f"💵 Потенциальный доход: {casino['income']:,}$ / 1h\n"
        f"⏱ Цикл дохода: 1h\n"
        f"⏳ До следующего цикла: {minutes:02d}:{seconds:02d}"
    )
    await call.message.edit_text(text, reply_markup=casino_main_kb(user_id))


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


@casinos_router.callback_query(F.data.startswith("casino_"))
async def casino_cb(call: types.CallbackQuery):
    if not await protect_owner(call):
        return

    user_id = call.from_user.id
    casino = get_casino(user_id)
    player = get_player(user_id, call.from_user.first_name)
    data = call.data

    # --- открыть казино ---
    if data.startswith("casino_open_"):
        if casino["status"] == "active":
            await call.answer("Казино уже открыто!", show_alert=True)
            return
        if casino["tables"] <= 0:
            await call.answer("❌ Нет столов для игры", show_alert=True)
            return
        casino["status"] = "active"
        casino["last_cycle"] = time.time()
        update_casino(user_id, casino)
        await call.answer("▶ Казино открыто! Клиенты приходят 🎲")
        await refresh_casino_menu(call, casino)

    # --- купить столы ---
    elif data.startswith("casino_buytables_"):
        if casino["tables"] >= casino["max_tables"]:
            await call.answer("⚠️ Уже полный зал столов", show_alert=True)
            return
        if player["money"] < TABLE_PRICE:
            await call.answer("❌ Недостаточно денег", show_alert=True)
            return
        player["money"] -= TABLE_PRICE
        casino["tables"] = casino["max_tables"]
        save_player(user_id, player)
        update_casino(user_id, casino)
        await call.answer("🎲 Столы закуплены!", show_alert=True)
        await refresh_casino_menu(call, casino)

    # --- забрать банк ---
    elif data.startswith("casino_take_"):
        if casino["cashbox"] <= 0:
            await call.answer("⚠️ Банк пустой!", show_alert=True)
            return
        player["biz_account"] += casino["cashbox"]
        casino["cashbox"] = 0
        save_player(user_id, player)
        update_casino(user_id, casino)
        await call.answer(f"+{player['biz_account']:,}$ зачислено на бизнес счёт", show_alert=True)
        await refresh_casino_menu(call, casino)

    # --- информация ---
    elif data.startswith("casino_info_"):
        mention = get_mention(user_id, call.from_user.first_name)
        upgrade = UPGRADES_CASINO[min(casino['level'], 3)]
        text = (
            "📊 СТАТУС КАЗИНО\n━━━━━━━━━━━━━━\n"
            f"👤 Владелец: {mention}\n"
            f"🎰 Тип: Казино\n"
            f"📈 Уровень: {casino['level']}/3\n"
            f"🎲 Столы: {casino['tables']} / {upgrade['max_tables']}\n"
            f"💰 В банке: {casino['cashbox']:,}$\n"
            f"💵 Потенциальный доход: {upgrade['income']:,}$ / 1h\n\n"
            f"📊 Всего заработано: {casino['total_earned']:,}$\n"
            f"⬆ Улучшений: {casino['upgrades']}/3"
        )
        await call.message.edit_text(text, reply_markup=casino_back_kb(user_id), parse_mode="HTML")

    # --- назад ---
    elif data.startswith("casino_back_"):
        await refresh_casino_menu(call, casino)

    # --- улучшения ---
    elif data.startswith("casino_upgrades_") or data.startswith("casino_upgrade_"):
        level = casino["level"]
        if data.startswith("casino_upgrade_"):
            if level >= 3:
                await call.answer("⚠️ Максимальный уровень", show_alert=True)
                return
            price = UPGRADES_CASINO[level + 1]["price"]
            if player["money"] < price:
                await call.answer("❌ Недостаточно денег", show_alert=True)
                return
            player["money"] -= price
            casino["level"] += 1
            casino["upgrades"] += 1
            upgrade = UPGRADES_CASINO[casino["level"]]
            casino["income"] = upgrade["income"]
            casino["max_tables"] = upgrade["max_tables"]
            casino["max_cash"] = upgrade["max_cash"]
            save_player(user_id, player)
            update_casino(user_id, casino)
            await call.answer("⬆ Казино улучшено!", show_alert=True)
            level = casino["level"]

        if level >= 3:
            text = "✅ Максимальный уровень!"
        else:
            next_upgrade = UPGRADES_CASINO[level + 1]
            text = (
                f"⬆ УЛУЧШЕНИЯ КАЗИНО {level+1}/3\n"
                "━━━━━━━━━━━━━━\n"
                f"💵 Доход: {next_upgrade['income']:,}$\n"
                f"🎲 Склад: {next_upgrade['max_tables']}\n"
                f"💰 Максимальный банк: {next_upgrade['max_cash']:,}$\n\n"
                f"Следующее улучшение:\n💰 Цена: {next_upgrade['price']:,}$\n"
                f"Уровень {level+2}"
            )
        await call.message.edit_text(text, reply_markup=casino_upgrades_kb(casino,user_id))
