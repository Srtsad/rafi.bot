import random
from aiogram import Router, types
from utils.helpers import get_player, save_player

router = Router()

# ==========================
# СПИСОК ЯХТ С КАТЕГОРИЯМИ
# ==========================
YACHTS_LIST = [
    {"name": "Маленькая моторка", "price": 10_000_000, "emoji": "🛥", "category": "Малые"},
    {"name": "Катер", "price": 20_000_000, "emoji": "🛥", "category": "Малые"},
    {"name": "Sunseeker 50", "price": 50_000_000, "emoji": "🛥", "category": "Средние"},
    {"name": "Azimut 55", "price": 100_000_000, "emoji": "🛥", "category": "Средние"},
    {"name": "Princess 60", "price": 200_000_000, "emoji": "🛥", "category": "Средние"},
    {"name": "Ferretti 70", "price": 400_000_000, "emoji": "🛥", "category": "Премиум"},
    {"name": "Sunseeker 100", "price": 700_000_000, "emoji": "🛥", "category": "Премиум"},
    {"name": "Mangusta 108", "price": 1_000_000_000, "emoji": "🛥", "category": "Премиум"},
    {"name": "Benetti 140", "price": 2_500_000_000, "emoji": "🛥", "category": "Супер-яхты"},
    {"name": "Lürssen 150", "price": 5_000_000_000, "emoji": "🛥", "category": "Супер-яхты"},
    {"name": "Oceanco 180", "price": 10_000_000_000, "emoji": "🛥", "category": "Супер-яхты"},
    {"name": "Feadship 200", "price": 20_000_000_000, "emoji": "🛥", "category": "Легендарные"},
    {"name": "Amels 210", "price": 40_000_000_000, "emoji": "🛥", "category": "Легендарные"},
    {"name": "Eclipse", "price": 70_000_000_000, "emoji": "🛥", "category": "Легендарные"},
    {"name": "History Supreme / Concept Yacht", "price": 150_000_000_000, "emoji": "🛥", "category": "Легендарные"},
]

# ==========================
# СПИСОК ЯХТ С КАТЕГОРИЯМИ
# ==========================
@router.message(lambda message: message.text and message.text.lower() in ["яхты", "яхта", "клуб"])
async def yachts_list(message: types.Message):
    categories = ["Малые", "Средние", "Премиум", "Супер-яхты", "Легендарные"]
    text = "🛥 <b>YACHT CLUB MARINA</b> 🛥\nДобро пожаловать в яхт-клуб!\nВыберите яхту по вашему статусу 💸\n\n"
    for cat in categories:
        text += f"📌 <b>{cat}</b>\n"
        for idx, yacht in enumerate(YACHTS_LIST, start=1):
            if yacht["category"] == cat:
                text += f"{idx}. {yacht['emoji']} {yacht['name']} — {yacht['price']:,}$\n"
        text += "\n"
    text += "🛒 Команды:\nКупить яхту [номер]\nПродать яхту [номер]\n"
    await message.answer(text, parse_mode="HTML")


# ==========================
# Купить яхту
# ==========================
@router.message(lambda message: message.text and message.text.lower().startswith("купить яхту"))
async def buy_yacht(message: types.Message):
    user = message.from_user
    player = get_player(user.id, username=user.first_name)

    parts = message.text.split()
    if len(parts) < 3 or not parts[2].isdigit():
        await message.answer("❌ Укажите номер яхты, например: <b>Купить яхту 1</b>")
        return

    yacht_idx = int(parts[2]) - 1
    if yacht_idx < 0 or yacht_idx >= len(YACHTS_LIST):
        await message.answer("❌ Неверный номер яхты.")
        return

    yacht = YACHTS_LIST[yacht_idx]
    price = yacht["price"]

    if player["money"] < price:
        await message.answer("❌ У вас недостаточно денег для покупки этой яхты.")
        return

    player["money"] -= price
    if "property" not in player:
        player["property"] = []

    player["property"].append({
        "type": "yacht",
        "name": yacht["name"],
        "price": price,
        "emoji": yacht["emoji"]
    })
    save_player(user.id, player)

    await message.answer(f"✅ Вы успешно купили яхту <b>{yacht['emoji']} {yacht['name']}</b> за <b>{price:,}$</b>!")


# ==========================
# Продать яхту
# ==========================
@router.message(lambda message: message.text and message.text.lower().startswith("продать яхту"))
async def sell_yacht(message: types.Message):
    user = message.from_user
    player = get_player(user.id, username=user.first_name)

    yachts = [p for p in player.get("property", []) if isinstance(p, dict) and p.get("type") == "yacht"]
    if not yachts:
        await message.answer("❌ У вас нет яхт.")
        return

    parts = message.text.split()
    if len(parts) < 3 or not parts[2].isdigit():
        await message.answer("❌ Укажите номер яхты из вашего имущества, например: <b>Продать яхту 1</b>")
        return

    yacht_idx = int(parts[2]) - 1
    if yacht_idx < 0 or yacht_idx >= len(yachts):
        await message.answer("❌ Неверный номер яхты.")
        return

    yacht = yachts[yacht_idx]
    refund = int(yacht["price"] * 0.79)

    player["money"] += refund
    player["property"].remove(yacht)
    save_player(user.id, player)

    await message.answer(
        f"💰 Вы продали яхту <b>{yacht['emoji']} {yacht['name']}</b> и получили <b>{refund:,}$</b> назад.")
