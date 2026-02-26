import json
from aiogram import Router, types
from utils.helpers import get_player, save_player

router = Router()

# нормализация текста (ё=е)
def norm(text: str):
    return text.lower().replace("ё", "е")

# ==========================
# СПИСОК МАШИН С ЭМОДЗИ И КАТЕГОРИЯМИ
# ==========================
CARS = {
    1: {"name": "Самокат", "price": 100_000, "emoji": "🛴", "category": "Обычные"},
    2: {"name": "Велосипед", "price": 500_000, "emoji": "🚲", "category": "Обычные"},
    3: {"name": "Электросамокат", "price": 1_000_000, "emoji": "🛴", "category": "Обычные"},
    4: {"name": "Гироскутер", "price": 2_500_000, "emoji": "🛹", "category": "Обычные"},
    5: {"name": "Сегвей", "price": 5_000_000, "emoji": "🛴", "category": "Обычные"},

    6: {"name": "Мопед", "price": 10_000_000, "emoji": "🏍", "category": "Двухколёсные"},
    7: {"name": "Скутер", "price": 20_000_000, "emoji": "🛵", "category": "Двухколёсные"},
    8: {"name": "Мотоцикл", "price": 35_000_000, "emoji": "🏍", "category": "Двухколёсные"},
    9: {"name": "Yamaha MT-07", "price": 50_000_000, "emoji": "🏍", "category": "Двухколёсные"},

    10: {"name": "ВАЗ 2109", "price": 75_000_000, "emoji": "🚗", "category": "Легковые"},
    11: {"name": "Lada Granta", "price": 100_000_000, "emoji": "🚘", "category": "Легковые"},
    12: {"name": "Квадроцикл", "price": 150_000_000, "emoji": "🚙", "category": "Легковые"},
    13: {"name": "Багги", "price": 250_000_000, "emoji": "🚗", "category": "Легковые"},
    14: {"name": "Toyota Corolla", "price": 500_000_000, "emoji": "🚘", "category": "Легковые"},
    15: {"name": "Вездеход", "price": 800_000_000, "emoji": "🚙", "category": "Легковые"},
    16: {"name": "Lada XRAY", "price": 1_200_000_000, "emoji": "🚗", "category": "Легковые"},

    17: {"name": "Kia Sportage", "price": 2_000_000_000, "emoji": "🚘", "category": "Премиум"},
    18: {"name": "Audi Q7", "price": 3_000_000_000, "emoji": "🚙", "category": "Премиум"},
    19: {"name": "BMW X6", "price": 5_000_000_000, "emoji": "🚗", "category": "Премиум"},
    20: {"name": "Mercedes-AMG GT", "price": 8_000_000_000, "emoji": "🏎", "category": "Премиум"},
    21: {"name": "Toyota Supra", "price": 12_000_000_000, "emoji": "🏎", "category": "Премиум"},
    22: {"name": "BMW Z4 M", "price": 18_000_000_000, "emoji": "🏎", "category": "Премиум"},
    23: {"name": "Subaru WRX STI", "price": 25_000_000_000, "emoji": "🏎", "category": "Премиум"},
    24: {"name": "Nissan GT-R", "price": 40_000_000_000, "emoji": "🏎", "category": "Премиум"},

    25: {"name": "Lamborghini Huracan", "price": 60_000_000_000, "emoji": "🔥", "category": "Гиперкары"},
    26: {"name": "Lamborghini Veneno", "price": 80_000_000_000, "emoji": "🔥", "category": "Гиперкары"},
    27: {"name": "Tesla Roadster", "price": 100_000_000_000, "emoji": "⚡", "category": "Гиперкары"},
    28: {"name": "Bugatti Chiron", "price": 120_000_000_000, "emoji": "👑", "category": "Гиперкары"},
    29: {"name": "Ferrari LaFerrari", "price": 130_000_000_000, "emoji": "👑", "category": "Гиперкары"},
    30: {"name": "Koenigsegg Jesko", "price": 140_000_000_000, "emoji": "👑", "category": "Гиперкары"},
    31: {"name": "Thrust SSC", "price": 150_000_000_000, "emoji": "🚀", "category": "Гиперкары"},
}

# ==========================
# СПИСОК МАШИН С КАТЕГОРИЯМИ
# ==========================
@router.message(lambda m: m.text and norm(m.text) in ["машина", "машины", "авто", "автомобили"])
async def cars_list(message: types.Message):
    categories = ["Обычные", "Двухколёсные", "Легковые", "Премиум", "Гиперкары"]
    text = "🚗 <b>АВТОГАЛАКТИКА</b> 🚗\nДобро пожаловать в наш автосалон! Выберите машину по бюджету 💸\n\n"
    for cat in categories:
        text += f"📌 <b>{cat}</b>\n"
        for idx, car in CARS.items():
            if car["category"] == cat:
                text += f"{idx}. {car['emoji']} {car['name']} — {car['price']:,}$\n"
        text += "\n"
    text += "🛒 Команды:\nКупить машину [номер]\nПродать машину [номер]\n"
    await message.answer(text, parse_mode="HTML")

# ==========================
# ПОКУПКА МАШИНЫ
# ==========================
@router.message(lambda m: m.text and norm(m.text).startswith("купить машину"))
async def buy_car(message: types.Message):
    user = message.from_user
    player = get_player(user.id, username=user.first_name)

    try:
        number = int(norm(message.text).split()[-1])
    except:
        await message.answer("❌ Пример: Купить машину 1")
        return

    if number not in CARS:
        await message.answer("❌ Нет такой машины.")
        return

    car = CARS[number]
    if player["money"] < car["price"]:
        await message.answer(f"❌ Недостаточно денег для {car['emoji']} {car['name']}")
        return

    player["money"] -= car["price"]
    if "property" not in player:
        player["property"] = []

    player["property"].append({
        "type": "car",
        "name": car["name"],
        "price": car["price"],
        "emoji": car["emoji"]
    })

    save_player(user.id, player)
    await message.answer(f"✅ Вы успешно купили машину {car['emoji']} {car['name']} за {car['price']:,}$!")

# ==========================
# ПРОДАЖА МАШИНЫ ПО НОМЕРУ В ИМУЩЕСТВЕ
# ==========================
@router.message(lambda m: m.text and norm(m.text).startswith("продать машину"))
async def sell_car(message: types.Message):
    user = message.from_user
    player = get_player(user.id, username=user.first_name)

    cars = [p for p in player.get("property", []) if isinstance(p, dict) and p.get("type") == "car"]
    if not cars:
        await message.answer("❌ У вас нет машин.")
        return

    try:
        number = int(norm(message.text).split()[-1])
    except:
        await message.answer("❌ Пример: Продать машину 1")
        return

    if number <= 0 or number > len(cars):
        await message.answer("❌ Неверный номер машины в вашем имуществе.")
        return

    car = cars[number - 1]
    refund = int(car["price"] * 0.79)
    player["money"] += refund
    player["property"].remove(car)
    save_player(user.id, player)

    await message.answer(f"💰 Вы продали машину {car['emoji']} {car['name']} и получили {refund:,}$ назад.")
