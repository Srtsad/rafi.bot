from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from keyboards.menu_keyboards import menu_categories

router = Router()

@router.message(Command("menu"))
@router.message(Command("help"))
async def menu_cmd(message: Message):
    user = message.from_user
    mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'

    text = (
        f"👋 <b>{mention}, выбери категорию:</b>\n\n"

        f"━━━━━━━━━━━━━━━\n"
        f"🧩 <b>Основное</b>\n"
        f"🎮 <b>Игры</b>\n"
        f"🎭 <b>Развлекательное</b>\n"
        f"🏰 <b>Кланы</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"

        f"💬 <a href='https://t.me/RafiChatfirst'><b>Общая беседа №1</b></a> — место для всех игроков\n"
        f"🆘 <a href='https://t.me/RafiSupportHelp'><b>Support</b></a> — помощь и вопросы"
    )

    await message.answer(
        text,
        reply_markup=menu_categories(),
        disable_web_page_preview=True
    )
