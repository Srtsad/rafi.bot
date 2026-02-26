from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def menu_categories():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Основное", callback_data="cat_main")],
            [InlineKeyboardButton(text="🎮 Игры", callback_data="cat_games")],
            [InlineKeyboardButton(text="🎭 Развлекательное", callback_data="cat_fun")],
            [InlineKeyboardButton(text="🛡 Кланы", callback_data="cat_clans")],
        ]
    )


def back_button():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ]
    )
