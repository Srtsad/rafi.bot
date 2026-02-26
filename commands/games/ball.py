# commands/games/ball.py

import random
from aiogram import Router, types
from utils.helpers import get_player

ball_router = Router()


def get_user_name(message: types.Message):
    user = message.from_user

    try:
        player = get_player(user.id)
        nickname = player.get("nickname")
    except:
        nickname = None

    if nickname:
        return f'<a href="tg://user?id={user.id}">🔮 {nickname}</a>'
    else:
        return f'<a href="tg://user?id={user.id}">🔮 Игрок</a>'


# ===== ПОДСКАЗКА ЕСЛИ ПРОСТО "ШАР" =====
@ball_router.message(lambda m: m.text and m.text.lower().strip() == "шар")
async def ball_help(message: types.Message):
    text = (
        "🔮 <b>МАГИЧЕСКИЙ ШАР</b>\n"
        "━━━━━━━━━━━━━━\n"
        "💭 Задай любой вопрос шару\n"
        "и получи ответ судьбы\n\n"
        "📌 <b>Как использовать:</b>\n"
        "Напиши:\n"
        "👉 <code>шар я стану богатым?</code>\n"
        "👉 <code>шар мне повезёт сегодня?</code>\n"
        "👉 <code>шар он напишет?</code>\n\n"
        "✨ Шар ответит честно..."
    )
    await message.answer(text, parse_mode="HTML")


# ===== ОСНОВНАЯ КОМАНДА =====
@ball_router.message(lambda m: m.text and m.text.lower().startswith("шар "))
async def magic_ball_cmd(message: types.Message):
    phrase = message.text[4:].strip()

    if not phrase:
        await message.answer(
            "🔮 <b>Напиши вопрос после слова шар</b>\n"
            "Пример:\n"
            "<code>шар я разбогатею?</code>",
            parse_mode="HTML"
        )
        return

    user_name = get_user_name(message)

    answers = [
        "Да.",
        "Нет.",
        "Скорее да.",
        "Скорее нет.",
        "100% да.",
        "Шанс огромный.",
        "Маловероятно.",
        "Попробуй позже.",
        "Вселенная говорит да.",
        "Вселенная говорит нет.",
        "Очень скоро.",
        "Не сегодня.",
        "Тебе повезёт.",
        "Сомневаюсь.",
        "Без вариантов.",
        "Определённо да.",
        "Тайна скрыта…",
        "Знаки положительные.",
        "Знаки плохие.",
        "Рискни."
    ]

    result = random.choice(answers)

    text = (
        f"{user_name}, шар думает... 🔮\n\n"
        f"❓ <b>Вопрос:</b> {phrase}\n"
        f"🔮 <b>Ответ:</b> {result}"
    )

    await message.answer(text, parse_mode="HTML")
