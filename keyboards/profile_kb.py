from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def profile_buttons(user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🏡 Имущество",
                callback_data=f"profile_property:{user_id}"
            )],
            [InlineKeyboardButton(
                text="💼 Бизнес",
                callback_data=f"profile_business:{user_id}"
            )]
        ]
    )


def back_to_profile(user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🔙 Назад к профилю",
                callback_data=f"profile_back:{user_id}"
            )]
        ]
    )
