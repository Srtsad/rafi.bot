from aiogram import Router, types
from utils.helpers import get_player, save_player, get_mention
import random
import time

router = Router()

# ---------------------------
# Настройки добычи
# ---------------------------
ENERGY_COST = 10  # энергия за одну добычу
COOLDOWN = 5      # секунда между добычами

# Список ресурсов с шансом выпадения и текстом
RESOURCES = [
    {"name": "железо", "chance": 40, "text": "🪨 Обычная находка\n⛓ Железо ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "золото", "chance": 10, "text": "🪨 Обычная находка\n🌕 Золото ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "никель", "chance": 6, "text": "🛠 Промышленная жила\n🪙 Никель ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "астролит", "chance": 3, "text": "🛠 Промышленная жила\n🛰 Астролит ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "алмаз", "chance": 5, "text": "💎 Редкая жила\n💎 Алмаз ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "аметист", "chance": 5, "text": "💎 Редкая жила\n🟣 Аметист ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "аквамарин", "chance": 4, "text": "💎 Редкая жила\n💠 Аквамарин ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "изумруд", "chance": 4, "text": "💎 Редкая жила\n🍀 Изумруд ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "кварциум", "chance": 3, "text": "⚡ Высокотехнологичный слой\n🔷 Кварциум ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "материя", "chance": 2, "text": "⚡ Высокотехнологичный слой\n🌌 Материя ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "плазма", "chance": 1, "text": "⚡ Высокотехнологичный слой\n💥 Плазма ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "нейронит", "chance": 1, "text": "⚡ Высокотехнологичный слой\n🧠 Нейронит ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "титан", "chance": 1, "text": "🧪 Экспериментальный слой\n⚙ Титан ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "кобальт", "chance": 1, "text": "🧪 Экспериментальный слой\n🔬 Кобальт ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "энергон", "chance": 1, "text": "🧪 Экспериментальный слой\n⚡ Энергон ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "эктоплазма", "chance": 0.5, "text": "🌑 Легендарная жила\n👻 Эктоплазма ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "хрононий", "chance": 0.5, "text": "🌑 Легендарная жила\n⏳ Хрононий ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "генезиум", "chance": 0.2, "text": "🌑 Легендарная жила\n🌠 Генезиум ×1\n📦 Добавлено\n⚡ −10 энергии"},
    {"name": "палладий", "chance": 0.1, "text": "🌑 Легендарная жила\n🏆 Палладий ×1\n📦 Добавлено\n⚡ −10 энергии"},
]

# ---------------------------
# Проверка возможности добычи
# ---------------------------
def can_mine(player):
    if player.get("energy",0) < ENERGY_COST:
        return False, "no_energy"
    now = time.time()
    if now - player.get("last_mine",0) < COOLDOWN:
        return False, "cooldown"
    return True, None

# ---------------------------
# Генерация одного ресурса
# ---------------------------
def mine_once():
    roll = random.uniform(0,100)
    cumulative = 0
    for res in RESOURCES:
        cumulative += res["chance"]
        if roll <= cumulative:
            return res["name"], res["text"]
    # Если не выпало ничего
    return None, "🌫 Пустая порода\n📦 Ничего не найдено\n⚡ −10 энергии"

# ---------------------------
# Команда копать руду
# ---------------------------
@router.message(lambda m: m.text and m.text.lower() == "копать руду")
async def cmd_mine(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    mention = get_mention(user_id, message.from_user.first_name)

    # Проверка энергии и кулдауна
    ok, reason = can_mine(player)
    if not ok:
        if reason == "no_energy":
            await message.answer(f"❌ Недостаточно энергии ({ENERGY_COST} нужно)")
        elif reason == "cooldown":
            await message.answer("⏳ Подожди, ты только что копал!")
        return

    # Генерация одного ресурса
    ore, text = mine_once()

    # Добавляем в инвентарь если что-то выпало
    if ore:
        player.setdefault("inventory", {})
        player["inventory"].setdefault("ores", {})
        player["inventory"]["ores"][ore] = player["inventory"]["ores"].get(ore,0) + 1

    # Снимаем энергию и сохраняем время последней добычи
    player["energy"] -= ENERGY_COST
    player["last_mine"] = time.time()
    save_player(user_id, player)

    await message.answer(text)
