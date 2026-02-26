import json
import os
from aiogram import Router, types
from utils.helpers import get_player, save_player

router = Router()

# нормализация текста (ё=е)
def norm(text: str):
    return text.lower().replace("ё", "е")

# ==========================
# СПИСОК ВЕРТОЛЁТОВ С КАТЕГОРИЯМИ
# ==========================
HELICOPTERS = [
    {"name": "Лёгкий Robinson R22", "price": 5_000_000, "emoji": "🚁", "category": "Малые"},
    {"name": "Robinson R44", "price": 10_000_000, "emoji": "🚁", "category": "Малые"},
    {"name": "Bell 206", "price": 20_000_000, "emoji": "🚁", "category": "Малые"},
    {"name": "Airbus H125", "price": 40_000_000, "emoji": "🚁", "category": "Средние"},
    {"name": "Bell 407", "price": 70_000_000, "emoji": "🚁", "category": "Средние"},
    {"name": "AgustaWestland AW109", "price": 100_000_000, "emoji": "🚁", "category": "Средние"},
    {"name": "Sikorsky S-76", "price": 200_000_000, "emoji": "🚁", "category": "Премиум"},
    {"name": "Eurocopter EC145", "price": 400_000_000, "emoji": "🚁", "category": "Премиум"},
    {"name": "Bell 429", "price": 600_000_000, "emoji": "🚁", "category": "Премиум"},
    {"name": "AgustaWestland AW139", "price": 1_000_000_000, "emoji": "🚁", "category": "Супер"},
    {"name": "Sikorsky S-92", "price": 2_000_000_000, "emoji": "🚁", "category": "Супер"},
    {"name": "Airbus H175", "price": 5_000_000_000, "emoji": "🚁", "category": "Супер"},
    {"name": "Mil Mi-26", "price": 10_000_000_000, "emoji": "🚁", "category": "Легендарные"},
    {"name": "Lockheed Martin VH-71", "price": 50_000_000_000, "emoji": "🚁", "category": "Легендарные"},
    {"name": "Супер-вертолёт", "price": 150_000_000_000, "emoji": "🚁", "category": "Легендарные"},
]

# ==========================
# СПИСОК
# ==========================
@router.message(lambda m: m.text and norm(m.text) in ["вертолет", "вертолеты"])
async def helicopters_list(message: types.Message):
    categories = ["Малые", "Средние", "Премиум", "Супер", "Легендарные"]
    text = "🚁 <b>HOWER HELICOPTER CLUB</b> 🚁\nДобро пожаловать в авиасалон!\nВыберите вертолёт по бюджету 💸\n\n"
    for cat in categories:
        text += f"📌 <b>{cat}</b>\n"
        for idx, heli in enumerate(HELICOPTERS, start=1):
            if heli["category"] == cat:
                text += f"{idx}. {heli['emoji']} {heli['name']} — {heli['price']:,}$\n"
        text += "\n"
    text += "🛒 Команды:\nКупить вертолет [номер]\nПродать вертолет [номер]\n"
    await message.answer(text, parse_mode="HTML")

# ==========================
# ПОКУПКА
# ==========================
@router.message(lambda m: m.text and norm(m.text).startswith("купить вертолет"))
async def buy_helicopter(message: types.Message):
    user = message.from_user
    player = get_player(user.id, username=user.first_name)

    try:
        number = int(norm(message.text).split()[-1])
    except:
        await message.answer("❌ Пример: Купить вертолет 1")
        return

    if number <= 0 or number > len(HELICOPTERS):
        await message.answer("❌ Нет такого вертолёта.")
        return

    heli = HELICOPTERS[number - 1]
    if player["money"] < heli["price"]:
        await message.answer("❌ Недостаточно денег.")
        return

    player["money"] -= heli["price"]
    if "property" not in player:
        player["property"] = []

    player["property"].append({
        "type": "helicopter",
        "name": heli["name"],
        "price": heli["price"],
        "emoji": heli["emoji"]
    })
    save_player(user.id, player)

    await message.answer(
        f"✅ Вы успешно купили вертолёт {heli['emoji']} {heli['name']} за {heli['price']:,}$!"
    )

# ==========================
# ПРОДАЖА
# ==========================
@router.message(lambda m: m.text and norm(m.text).startswith("продать вертолет"))
async def sell_helicopter(message: types.Message):
    user = message.from_user
    player = get_player(user.id, username=user.first_name)

    helicopters = [p for p in player.get("property", []) if isinstance(p, dict) and p.get("type") == "helicopter"]
    if not helicopters:
        await message.answer("❌ У вас нет вертолётов.")
        return

    try:
        number = int(norm(message.text).split()[-1])
    except:
        await message.answer("❌ Пример: Продать вертолет 1")
        return

    if number <= 0 or number > len(helicopters):
        await message.answer("❌ Неверный номер.")
        return

    heli = helicopters[number - 1]
    sell_price = int(heli["price"] * 0.79)

    player["money"] += sell_price
    player["property"].remove(heli)
    save_player(user.id, player)

    await message.answer(
        f"💰 Вы продали вертолёт {heli['emoji']} {heli['name']} и получили {sell_price:,}$ назад."
    )
