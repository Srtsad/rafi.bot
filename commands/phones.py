from aiogram import Router, types
from utils.helpers import get_player, save_player

router = Router()

# ==========================
# Список телефонов
# ==========================
PHONES = [
    {"name": "Nokia 3310", "price": 10_000},
    {"name": "Samsung A01", "price": 50_000},
    {"name": "Redmi 9A", "price": 100_000},
    {"name": "iPhone SE", "price": 200_000},
    {"name": "Samsung A12", "price": 400_000},
    {"name": "Redmi Note 12", "price": 700_000},
    {"name": "iPhone 12", "price": 1_000_000},
    {"name": "Galaxy S21", "price": 2_000_000},
    {"name": "iPhone 13", "price": 4_000_000},
    {"name": "S22 Ultra", "price": 6_000_000},
    {"name": "iPhone 14", "price": 10_000_000},
    {"name": "Z Flip 4", "price": 15_000_000},
    {"name": "iPhone 14 Pro", "price": 20_000_000},
    {"name": "Z Fold 5", "price": 30_000_000},
    {"name": "iPhone 15", "price": 50_000_000},
    {"name": "iPhone 15 Pro", "price": 70_000_000},
    {"name": "iPhone 16", "price": 100_000_000},
    {"name": "iPhone 16 Pro", "price": 150_000_000},
    {"name": "iPhone 17", "price": 200_000_000},
    {"name": "iPhone 17 Pro", "price": 300_000_000},
    {"name": "iPhone 18", "price": 400_000_000},
    {"name": "iPhone 18 Pro", "price": 500_000_000},
    {"name": "iPhone 19", "price": 600_000_000},
    {"name": "iPhone 19 Pro", "price": 700_000_000},
    {"name": "iPhone 20", "price": 800_000_000},
    {"name": "iPhone 20 Pro", "price": 850_000_000},
    {"name": "Galaxy S23", "price": 900_000_000},
    {"name": "Galaxy S23+", "price": 925_000_000},
    {"name": "Galaxy S23 Ultra", "price": 950_000_000},
    {"name": "iPhone 21", "price": 1_000_000_000},
]

# ==========================
# Показать список телефонов
# ==========================
@router.message(lambda message: message.text and message.text.lower().strip() == "телефоны")
async def show_phones(message: types.Message):
    text = """
📱 <b>ТЕХНО</b> 📱
Добро пожаловать в магазин ТЕХНО!
Выбери устройство по своему статусу и бюджету 💸

━━━━━━━━━━━━━━
<b>📱 Доступные телефоны:</b>
━━━━━━━━━━━━━━
"""
    categories = ["Бюджетные", "Средний класс", "Премиум", "Люкс", "Элитные"]
    for cat in categories:
        text += f"\n<b>{cat}</b>\n"
        for idx, phone in enumerate(PHONES, start=1):
            # Определяем категории по цене
            if cat == "Бюджетные" and idx <= 6:
                text += f"{idx}. 📱 <b>{phone['name']}</b> — <b>{phone['price']:,}$</b>\n"
            elif cat == "Средний класс" and 7 <= idx <= 12:
                text += f"{idx}. 📱 <b>{phone['name']}</b> — <b>{phone['price']:,}$</b>\n"
            elif cat == "Премиум" and 13 <= idx <= 16:
                text += f"{idx}. 📱 <b>{phone['name']}</b> — <b>{phone['price']:,}$</b>\n"
            elif cat == "Люкс" and 17 <= idx <= 22:
                text += f"{idx}. 📱 <b>{phone['name']}</b> — <b>{phone['price']:,}$</b>\n"
            elif cat == "Элитные" and 23 <= idx <= 30:
                text += f"{idx}. 📱 <b>{phone['name']}</b> — <b>{phone['price']:,}$</b>\n"

    text += """
━━━━━━━━━━━━━━
🛒 <b>Покупка:</b>
Купить телефон [номер]
💸 <b>Продажа:</b>
Продать телефон [номер]
━━━━━━━━━━━━━━
"""
    await message.answer(text, parse_mode="HTML")

# ==========================
# Купить телефон
# ==========================
@router.message(lambda message: message.text and message.text.lower().startswith("купить телефон"))
async def buy_phone(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, username=message.from_user.first_name)

    try:
        number = int(message.text.strip().split()[-1])
    except:
        await message.answer("❌ Пример: Купить телефон [номер]")
        return

    if number < 1 or number > len(PHONES):
        await message.answer("❌ Телефона с таким номером нет!")
        return

    phone = PHONES[number - 1]

    if player["money"] < phone["price"]:
        await message.answer(
            f"❌ У вас недостаточно денег для покупки <b>{phone['name']}</b>!\n"
            f"💰 Требуется: <b>{phone['price']:,}$</b>, у вас: <b>{player['money']:,}$</b>",
            parse_mode="HTML"
        )
        return

    player["money"] -= phone["price"]
    player.setdefault("property", [])
    player["property"].append({
        "type": "phone",
        "name": phone["name"],
        "price": phone["price"],
        "emoji": "📱"
    })
    save_player(user_id, player)

    await message.answer(
        f"✅ Вы успешно купили телефон 📱 {phone['name']} за {phone['price']:,}$!",
        parse_mode="HTML"
    )

# ==========================
# Продать телефон
# ==========================
@router.message(lambda message: message.text and message.text.lower().startswith("продать телефон"))
async def sell_phone(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id)

    try:
        number = int(message.text.strip().split()[-1])
    except:
        await message.answer("❌ Пример: Продать телефон [номер]")
        return

    if "property" not in player or number <= 0 or number > len(player["property"]):
        await message.answer("❌ Неверный номер имущества.")
        return

    item = player["property"][number - 1]

    if not isinstance(item, dict) or item.get("type") != "phone":
        await message.answer("❌ На этом месте в имуществе нет телефона.")
        return

    refund = int(item["price"] * 0.79)
    player["money"] += refund
    removed_phone = player["property"].pop(number - 1)
    save_player(user_id, player)

    await message.answer(
        f"💰 Вы продали телефон 📱 {removed_phone['name']} и получили {refund:,}$ назад.",
        parse_mode="HTML"
    )
