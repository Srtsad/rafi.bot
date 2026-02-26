from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def start_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить бота в чат",
                    url="https://t.me/RafiBot?startgroup=true"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Общая беседа",
                    url="https://t.me/RafiChatfirst"
                ),
                InlineKeyboardButton(
                    text="🛠 Support",
                    url="https://t.me/RafiSupportHelp"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Наш канал",
                    url="https://t.me/RafiNews"
                )
            ]
        ]
    )
