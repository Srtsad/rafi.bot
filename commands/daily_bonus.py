from aiogram import Router, types
import random
import time
from utils.helpers import get_player, save_player  # твои функции

router = Router()
BONUS_COOLDOWN = 24 * 60 * 60  # 24 часа

# ----------------------
# Команда ежедневного бонуса
# ----------------------
@router.message(lambda message: message.text and message.text.lower().strip() in ["бонус", "ежедневный бонус"])
async def daily_bonus_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    player = get_player(user_id, username)

    now = time.time()
    last_time = player.get("last_bonus_time") or 0  # <-- исправлено

    if now - last_time < BONUS_COOLDOWN:
        remaining = BONUS_COOLDOWN - (now - last_time)
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        await message.answer(
            f"⏳ Бонус можно получать раз в 24 часа.\n"
            f"Вернитесь через {hours}ч {minutes}мин!"
        )
        return

    # Выдаём бонус
    if random.choice([True, False]):
        money = random.randint(500_000, 5_000_000)
        player["money"] += money
        text = f"🎉 Поздравляем! Вы получили 💸 {money:,} монет!\nПриходите завтра за новым бонусом!"
    else:
        exp = random.randint(50, 300)
        player["exp"] += exp
        text = f"✨ Отлично! Вы получили 💪🏽 {exp} Силы!\nВозвращайтесь через 24 часа за новым бонусом!"

    # Обновляем таймер
    player["last_bonus_time"] = now

    # Сохраняем игрока
    save_player(user_id, player)

    await message.answer(text, parse_mode="Markdown")

# ----------------------
# Команда сброса бонуса
# ----------------------
@router.message(lambda message: message.text and message.text.lower().strip() == "сброс бонуса")
async def reset_bonus_command(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id)
    player["last_bonus_time"] = 0  # обнуляем таймер
    save_player(user_id, player)
    await message.answer("⏰ Таймер бонуса обнулён! Можете получить его снова.")
