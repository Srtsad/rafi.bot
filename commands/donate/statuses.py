from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F  # Для фильтров текста

statuses_router = Router()

# Кнопка "Назад в меню"
def back_to_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="donate_back")]
        ]
    )

# Обработчик по тексту "статусы" (без import Text)
@statuses_router.message(F.text.casefold() == "статусы")
async def show_statuses(message: types.Message):
    text = """
━━━━━━━━━━━━━━━━━━

🏆 ДОНАТ-СТАТУСЫ (VIP)
━━━━━━━━━━━━━━━━━━
⏳ Срок действия — 15 дней
🎁 Активируется при покупке
🔄 Повторная покупка продлевает срок

🎩 Standart VIP — 75 Raf-Coin
━━━━━━━━━━━━━━
💰 Депозит: 8%
🏦 Налог снятия: 4.5%
⚡ Энергия: 30
🎁 Кейсы: 25
🎯 Повышенный шанс в играх
🔁 Передача: 1e24$ / сутки

📀 Gold VIP — 150 Raf-Coin
━━━━━━━━━━━━━━
💰 Депозит: 10%
🏦 Налог снятия: 3.5%
⚡ Энергия: 60
🎁 Кейсы: 50
🎁 Золотой ежедневный бонус
🔁 Передача: 5e24$ / сутки

💿 Platinum VIP — 270 Raf-Coin
━━━━━━━━━━━━━━
💰 Депозит: 12%
🏦 Налог снятия: 3%
⚡ Энергия: 90
🎁 Кейсы: 80
📈 ×2 опыт и добыча
🔁 Передача: 2e25$ / сутки

👑 Legendary VIP — 500 Raf-Coin
━━━━━━━━━━━━━━
💰 Депозит: 15%
🏦 Налог снятия: 2.5%
⚡ Энергия: 130
🎁 Кейсы: 150
📈 ×2.5 опыт
🏭 ×2 доход бизнесов
🔁 Передача: 1e26$ / сутки

━━━━━━━━━━━━━━━━━━
🛒 Команда: Купить привилегию [название]
━━━━━━━━━━━━━━━━━━
"""
    await message.answer(text, reply_markup=back_to_menu_keyboard())

# Обработчик кнопки "Назад в меню"
@statuses_router.callback_query(F.data == "donate_back")
async def back_to_donate_menu(cb: types.CallbackQuery):
    from commands.donate.donate import donate_keyboard  # Импорт меню доната
    await cb.message.edit_text("💎 Выберите категорию:", reply_markup=donate_keyboard())
