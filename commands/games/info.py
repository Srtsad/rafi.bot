# commands/games/info.py

import random
from aiogram import Router, types
from utils.helpers import get_player

info_router = Router()


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


# ===== ЕСЛИ ПРОСТО "ИНФА" =====
@info_router.message(lambda m: m.text and m.text.lower().strip() == "инфа")
async def info_help(message: types.Message):
    text = (
        "🔮 <b>КОМАНДА ИНФА</b>\n"
        "━━━━━━━━━━━━━━\n"
        "Хочешь узнать шанс события?\n"
        "Бот покажет процент.\n\n"
        "📌 <b>Как использовать:</b>\n"
        "Напиши вопрос после слова <b>инфа</b>\n\n"
        "👉 <code>инфа я разбогатею?</code>\n"
        "👉 <code>инфа он ответит?</code>\n"
        "👉 <code>инфа сегодня повезёт?</code>\n\n"
        "✨ Я покажу шанс от 0 до 100%"
    )
    await message.answer(text, parse_mode="HTML")


# ===== ОСНОВНАЯ КОМАНДА =====
@info_router.message(lambda m: m.text and m.text.lower().startswith("инфа "))
async def info_cmd(message: types.Message):
    phrase = message.text[5:].strip()

    if not phrase:
        await message.answer(
            "❌ <b>Напиши вопрос после команды</b>\n\n"
            "Пример:\n"
            "<code>инфа я стану богатым?</code>",
            parse_mode="HTML"
        )
        return

    user_name = get_user_name(message)
    percent = random.randint(0, 100)

    # разные ответы
    if percent <= 10:
        text = f"{user_name}, шанс: <b>{percent}%</b>\n💀 вообще без шансов"
    elif percent <= 30:
        text = f"{user_name}, шанс: <b>{percent}%</b>\n🤨 слабовато"
    elif percent <= 50:
        text = f"{user_name}, шанс: <b>{percent}%</b>\n😐 возможно"
    elif percent <= 70:
        text = f"{user_name}, шанс: <b>{percent}%</b>\n🙂 уже неплохо"
    elif percent <= 90:
        text = f"{user_name}, шанс: <b>{percent}%</b>\n🔥 почти уверен"
    else:
        text = f"{user_name}, шанс: <b>{percent}%</b>\n👑 100% тема"

    await message.answer(
        f"🔮 <b>Инфа на:</b> <b>{phrase}</b>\n\n{text}",
        parse_mode="HTML"
    )
