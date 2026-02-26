import json
from aiogram import Router, types
from utils.helpers import get_player, save_player

router = Router()

# нормализация текста (ё=е)
def norm(text: str):
    return text.lower().replace("ё", "е")

# СПИСОК САМОЛЁТОВ
PLANES = {
    1: {"name": "✈ Лёгкий дельтаплан", "price": 2_000_000},
    2: {"name": "✈ Планер", "price": 10_000_000},
    3: {"name": "✈ Cessna 172", "price": 20_000_000},
    4: {"name": "✈ Piper PA-28", "price": 50_000_000},
    5: {"name": "✈ Cirrus SR22", "price": 100_000_000},
    6: {"name": "✈ Pilatus PC-12", "price": 240_000_000},
    7: {"name": "✈ Cessna Citation M2", "price": 500_000_000},
    8: {"name": "✈ Embraer Phenom 300", "price": 1_000_000_000},
    9: {"name": "✈ Gulfstream G200", "price": 1_600_000_000},
    10: {"name": "✈ Bombardier Challenger 350", "price": 2_600_000_000},
}

# =========================
# СПИСОК
# =========================
@router.message(lambda m: m.text and norm(m.text) in ["самолет", "самолеты", "самолёт", "самолёты"])
async def planes_list(message: types.Message):
    text = "✈ <b>AVIASALON</b> ✈\nВыберите самолёт по бюджету 💸\n\n"
    for idx, plane in PLANES.items():
        text += f"{idx}. {plane['name']} — {plane['price']:,}$\n"
    text += "\n🛒 Команды:\nКупить самолёт [номер]\nПродать самолёт [номер]\n"
    await message.answer(text, parse_mode="HTML")

# =========================
# ПОКУПКА
# =========================
@router.message(lambda m: m.text and (norm(m.text).startswith("купить самолет") or norm(m.text).startswith("купить самолёт")))
async def buy_plane(message: types.Message):
    user = message.from_user
    player = get_player(user.id, username=user.first_name)

    try:
        number = int(norm(message.text).split()[-1])
    except:
        await message.answer("❌ Пример: Купить самолёт 1")
        return

    if number not in PLANES:
        await message.answer("❌ Нет такого самолёта.")
        return

    plane = PLANES[number]
    if player["money"] < plane["price"]:
        await message.answer(f"❌ Недостаточно денег для {plane['name']}")
        return

    player["money"] -= plane["price"]
    if "property" not in player:
        player["property"] = []

    # сохраняем самолёт
    player["property"].append({
        "type": "plane",
        "name": plane["name"],
        "price": plane["price"]
    })

    save_player(user.id, player)
    await message.answer(f"✅ Вы успешно купили самолёт {plane['name']} за {plane['price']:,}$!")

# =========================
# ПРОДАЖА САМОЛЁТА ПО НОМЕРУ В ИМУЩЕСТВЕ
# =========================
@router.message(lambda m: m.text and (norm(m.text).startswith("продать самолет") or norm(m.text).startswith("продать самолёт")))
async def sell_plane(message: types.Message):
    user = message.from_user
    player = get_player(user.id, username=user.first_name)

    if "property" not in player or not player["property"]:
        await message.answer("❌ У вас нет самолётов.")
        return

    # список только самолётов
    planes = [p for p in player["property"] if isinstance(p, dict) and p.get("type") == "plane"]

    if not planes:
        await message.answer("❌ У вас нет самолётов.")
        return

    # проверка номера из команды
    try:
        number = int(norm(message.text).split()[-1])
    except:
        await message.answer("❌ Пример: Продать самолёт [номер]")
        return

    if number <= 0 or number > len(planes):
        await message.answer("❌ Неверный номер. Номер указан в имуществе.")
        return

    plane = planes[number - 1]
    sell_price = int(plane["price"] * 0.79)
    player["money"] += sell_price
    # удаляем именно этот самолёт
    player["property"].remove(plane)
    save_player(user.id, player)

    await message.answer(f"💰 Вы продали самолёт {plane['name']} и получили {sell_price:,}$ назад.")
