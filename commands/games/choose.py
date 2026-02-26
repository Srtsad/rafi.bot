# commands/games/choose.py

import random
from aiogram import Router, types
from utils.helpers import get_player

choose_router = Router()


def get_user_name(message: types.Message):
    """Кликабельное имя или Игрок"""
    user = message.from_user

    try:
        player = get_player(user.id)
        nickname = player.get("nickname")
    except:
        nickname = None

    if nickname:
        return f'<a href="tg://user?id={user.id}">🧑 {nickname}</a>'
    else:
        return f'<a href="tg://user?id={user.id}">🧑 Игрок</a>'


# ===== ЕСЛИ ПРОСТО "ВЫБЕРИ" =====
@choose_router.message(lambda m: m.text and m.text.lower().strip() == "выбери")
async def choose_help(message: types.Message):
    text = (
        "🎯 <b>КОМАНДА ВЫБОРА</b>\n"
        "━━━━━━━━━━━━━━\n"
        "🤔 Не знаешь что выбрать?\n"
        "Бот решит за тебя.\n\n"
        "📌 <b>Как использовать:</b>\n"
        "Напиши варианты через <b>или</b>\n\n"
        "👉 <code>выбери пицца или суши</code>\n"
        "👉 <code>выбери играть или спать</code>\n"
        "👉 <code>выбери айфон или пк</code>\n\n"
        "✨ Я выберу лучший вариант"
    )
    await message.answer(text, parse_mode="HTML")


# ===== ОСНОВНАЯ КОМАНДА =====
@choose_router.message(lambda m: m.text and m.text.lower().startswith("выбери "))
async def choose_cmd(message: types.Message):
    text = message.text[7:].strip()

    if " или " not in text:
        await message.answer(
            "❌ <b>Напиши варианты через 'или'</b>\n\n"
            "Пример:\n"
            "<code>выбери пицца или суши</code>",
            parse_mode="HTML"
        )
        return

    variants = [v.strip() for v in text.split(" или ") if v.strip()]
    if len(variants) < 2:
        await message.answer("❌ Нужно минимум 2 варианта.", parse_mode="HTML")
        return

    result = random.choice(variants)
    user_name = get_user_name(message)

    answers = [
        f"{user_name}, думаю что 👉 <b>{result}</b>",
        f"{user_name}, мой выбор пал на 🔥 <b>{result}</b>",
        f"{user_name}, хмм... беру 🎯 <b>{result}</b>",
        f"{user_name}, интуиция говорит выбрать 💭 <b>{result}</b>",
        f"{user_name}, вселенная решила — ✨ <b>{result}</b>",
        f"{user_name}, 100% лучший вариант это 🏆 <b>{result}</b>",
        f"{user_name}, не думай даже... бери 😎 <b>{result}</b>",
    ]

    final_text = random.choice(answers)
    await message.answer(final_text, parse_mode="HTML")
