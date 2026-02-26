import json
import os
from aiogram import Router, types
from utils.helpers import get_player, save_player

router = Router()

# нормализация текста (ё=е)
def norm(text: str):
    return text.lower().replace("ё", "е")

# ==========================
# СПИСОК ДОМОВ С КАТЕГОРИЯМИ
# ==========================
HOUSES = [
    {"name": "Квартира-студия", "price": 500_000, "emoji": "🏠", "category": "Малые"},
    {"name": "Однокомнатная квартира", "price": 1_000_000, "emoji": "🏠", "category": "Малые"},
    {"name": "Двухкомнатная квартира", "price": 2_000_000, "emoji": "🏠", "category": "Малые"},
    {"name": "Трёхкомнатная квартира", "price": 3_500_000, "emoji": "🏠", "category": "Средние"},
    {"name": "Маленький дом", "price": 5_000_000, "emoji": "🏠", "category": "Средние"},
    {"name": "Дом с участком", "price": 10_000_000, "emoji": "🏠", "category": "Средние"},
    {"name": "Современный коттедж", "price": 20_000_000, "emoji": "🏠", "category": "Премиум"},
    {"name": "Вилла", "price": 35_000_000, "emoji": "🏠", "category": "Премиум"},
    {"name": "Вилла с бассейном", "price": 50_000_000, "emoji": "🏠", "category": "Премиум"},
    {"name": "Особняк", "price": 70_000_000, "emoji": "🏠", "category": "Супер"},
    {"name": "Особняк с садом", "price": 100_000_000, "emoji": "🏠", "category": "Супер"},
    {"name": "Летний дом", "price": 150_000_000, "emoji": "🏠", "category": "Супер"},
    {"name": "Загородная усадьба", "price": 200_000_000, "emoji": "🏠", "category": "Легендарные"},
    {"name": "Современный пентхаус", "price": 250_000_000, "emoji": "🏠", "category": "Легендарные"},
    {"name": "Лофт", "price": 300_000_000, "emoji": "🏠", "category": "Легендарные"},
    {"name": "Большая вилла", "price": 400_000_000, "emoji": "🏠", "category": "Элитные"},
    {"name": "Замок", "price": 500_000_000, "emoji": "🏰", "category": "Элитные"},
    {"name": "Особняк у моря", "price": 600_000_000, "emoji": "🏖️", "category": "Элитные"},
    {"name": "Пентхаус с видом на океан", "price": 700_000_000, "emoji": "🌊", "category": "Элитные"},
    {"name": "Супервилла", "price": 800_000_000, "emoji": "🏡", "category": "Элитные"},
    {"name": "Дворец", "price": 1_000_000_000, "emoji": "🏰", "category": "Королевские"},
    {"name": "Легендарный особняк", "price": 2_000_000_000, "emoji": "🏰", "category": "Королевские"},
    {"name": "Замок эпохи Ренессанс", "price": 5_000_000_000, "emoji": "🏰", "category": "Королевские"},
    {"name": "Супердорогой пентхаус", "price": 10_000_000_000, "emoji": "🏙️", "category": "Королевские"},
    {"name": "Дворец с золотым интерьером", "price": 20_000_000_000, "emoji": "👑", "category": "Королевские"},
    {"name": "Современный небоскрёб", "price": 40_000_000_000, "emoji": "🏢", "category": "Мега"},
    {"name": "Легендарная вилла", "price": 70_000_000_000, "emoji": "🏰", "category": "Мега"},
    {"name": "Императорский дворец", "price": 100_000_000_000, "emoji": "🏯", "category": "Мега"},
    {"name": "Сверхдорогой замок", "price": 130_000_000_000, "emoji": "🏰", "category": "Мега"},
    {"name": "Легендарный дворец / концепт", "price": 150_000_000_000, "emoji": "🏯", "category": "Мега"},
]

# ==========================
# СПИСОК С КАТЕГОРИЯМИ
# ==========================
@router.message(lambda m: m.text and norm(m.text) in ["дом", "дома"])
async def houses_list(message: types.Message):
    categories = ["Малые", "Средние", "Премиум", "Супер", "Легендарные", "Элитные", "Королевские", "Мега"]
    text = "🏠 <b>MANOR HOUSE CLUB</b> 🏠\nДобро пожаловать в MANOR!\nВыберите дом по бюджету 💸\n\n"
    for cat in categories:
        text += f"📌 <b>{cat}</b>\n"
        for idx, house in enumerate(HOUSES, start=1):
            if house["category"] == cat:
                text += f"{idx}. {house['emoji']} {house['name']} — {house['price']:,}$\n"
        text += "\n"
    text += "🛒 Команды:\nКупить дом [номер]\nПродать дом [номер]\n"
    await message.answer(text, parse_mode="HTML")


# ==========================
# ПОКУПКА
# ==========================
@router.message(lambda m: m.text and norm(m.text).startswith("купить дом"))
async def buy_house(message: types.Message):
    user = message.from_user
    player = get_player(user.id, username=user.first_name)

    try:
        number = int(norm(message.text).split()[-1])
    except:
        await message.answer("❌ Пример: Купить дом 1")
        return

    if number <= 0 or number > len(HOUSES):
        await message.answer("❌ Нет такого дома.")
        return

    house = HOUSES[number - 1]
    if player["money"] < house["price"]:
        await message.answer("❌ Недостаточно денег.")
        return

    player["money"] -= house["price"]
    if "property" not in player:
        player["property"] = []

    player["property"].append({
        "type": "house",
        "name": house["name"],
        "price": house["price"],
        "emoji": house["emoji"]
    })
    save_player(user.id, player)

    await message.answer(
        f"✅ Вы успешно купили {house['emoji']} {house['name']} за {house['price']:,}$!"
    )

# ==========================
# ПРОДАЖА
# ==========================
@router.message(lambda m: m.text and norm(m.text).startswith("продать дом"))
async def sell_house(message: types.Message):
    user = message.from_user
    player = get_player(user.id, username=user.first_name)

    houses = [p for p in player.get("property", []) if isinstance(p, dict) and p.get("type") == "house"]
    if not houses:
        await message.answer("❌ У вас нет домов.")
        return

    try:
        number = int(norm(message.text).split()[-1])
    except:
        await message.answer("❌ Пример: Продать дом 1")
        return

    if number <= 0 or number > len(houses):
        await message.answer("❌ Неверный номер.")
        return

    house = houses[number - 1]
    sell_price = int(house["price"] * 0.79)

    player["money"] += sell_price
    player["property"].remove(house)
    save_player(user.id, player)

    await message.answer(
        f"💰 Вы продали {house['emoji']} {house['name']} и получили {sell_price:,}$ назад."
    )
