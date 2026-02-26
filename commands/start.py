from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.main_menu import start_keyboard

router = Router()

# кнопки под стартом
def start_links():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Общая беседа", url="https://t.me/RafiChatfirst")]
    ])
    return kb

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    user = message.from_user
    mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'

    text = (
        f"🐲 <b>Привет, {mention}!</b>\n\n"

        f"🤖 <b>Rafi</b> — игровой движок <b>нового поколения</b> 🎮\n"
        f"<i>Место, где начинается настоящее игровое движение.</i>\n\n"

        f"━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Что тебя ждёт:</b>\n"
        f"• 🎮 Мини-игры и дуэли\n"
        f"• 🏹 Охота и прокачка\n"
        f"• 💼 Форбс-бизнесы\n"
        f"• 🏆 Рейтинг игроков\n"
        f"• 🎁 Награды и события\n"
        f"━━━━━━━━━━━━━━━\n\n"

        f"👥 <b>Играй один или с друзьями</b>\n"
        f"💰 Зарабатывай и прокачивайся\n"
        f"👑 Стань легендой сервера\n\n"

        f"📜 <b>Все команды:</b> /help\n\n"
        f"🚀 <b>Игровой режим активирован</b>"
    )

    await message.answer(
        text,
        reply_markup=start_keyboard()
    )

    # отдельная кнопка чат
    await message.answer(
        "👇 <b>Общайся с игроками:</b>",
        reply_markup=start_links()
    )
