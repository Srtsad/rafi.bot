import json
import os
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

donate_router = Router()

DB = "database-donate/donate.json"

def load_db():
    if not os.path.exists("database-donate"):
        os.makedirs("database-donate")

    if not os.path.exists(DB):
        with open(DB, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(DB, "r", encoding="utf-8") as f:
        return json.load(f)

def get_donate(user_id: int):
    data = load_db()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {
            "raf-coin": 0
        }
        with open(DB, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    return data[uid]

# Пример данных пользователя
def get_user_data(user_id):
    donate = get_donate(user_id)

    return {
        "ник": f"{user_id}",
        "статус": "Standart VIP",
        "raf-coin": donate["raf-coin"]
    }


# Главное меню доната
def donate_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Наш магазин", callback_data="donate_shop")],
            [InlineKeyboardButton(text="⭐ Донат через звезды", callback_data="donate_stars")],
            [InlineKeyboardButton(text="🌐 Донат через сайт", callback_data="donate_site")]
        ]
    )

# Кнопки внутри магазина
def shop_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏆 Статусы VIP", callback_data="donate_statuses")],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="donate_back")]
        ]
    )

# Кнопка назад в меню для статусов
def back_to_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="donate_back")]
        ]
    )

# Текст статусов
def statuses_text():
    return """
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

# Команда /донат
@donate_router.message(Command(commands=["donate"]))
async def donate_command(message: types.Message):
    await message.answer("💎 Выберите категорию:", reply_markup=donate_keyboard())

@donate_router.message(F.text.casefold() == "донат")
async def donate_text(message: types.Message):
    await donate_command(message)

# Обработка callback
@donate_router.callback_query(lambda c: c.data.startswith("donate_"))
async def donate_callback(cb: types.CallbackQuery):
    data = cb.data
    user_data = get_user_data(cb.from_user.id)

    if data == "donate_shop":
        text = f"""
━━━━━━━━━━━━━━━━━━
🛒 RAFI BOT — ДОНАТ МАГАЗИН
━━━━━━━━━━━━━━━━━━
👤 Пользователь: <a href="tg://user?id={cb.from_user.id}">{user_data['ник']}</a>
🎖 Статус: {user_data['статус']}
🪙 Raf-Coin: {user_data['raf-coin']}
━━━━━━━━━━━━━━━━━━
💱 Обмен коинов
━━━━━━━━━━━━━━━━━━
💵 Текущий курс: 1 RUB = 3 Raf-Coin
💸 1 Raf-Coin = 4.000.000$
🔄 Команда:
➜ Обменять [количество]
━━━━━━━━━━━━━━━━━━
🏆 Статусы
━━━━━━━━━━━━━━━━━━
🎩 Standart VIP — 75 Raf-Coin
📀 Gold VIP — 150 Raf-Coin
💿 Platinum VIP — 270 Raf-Coin
👑 Legendary — 500 Raf-Coin
🔝 Покупка:
➜ Купить привилегию [номер]
━━━━━━━━━━━━━━━━━━
⚡ Бустеры
━━━━━━━━━━━━━━━━━━
🚀 ×2 доход на 1 час — 120 Raf-Coin
🎯 +25% к редкому дропу — 90 Raf-Coin
🔥 ×3 добыча на 30 мин — 150 Raf-Coin
⏱ Сброс кулдаунов — 60 Raf-Coin
➜ Купить буст [номер]
━━━━━━━━━━━━━━━━━━
🎁 Кейсы
━━━━━━━━━━━━━━━━━━
📦 Обычный — 50 Raf-Coin
💠 Редкий — 140 Raf-Coin
👑 VIP — 300 Raf-Coin
➜ Купить кейс [номер]
━━━━━━━━━━━━━━━━━━
"""
        await cb.message.edit_text(text, reply_markup=shop_keyboard(), parse_mode="HTML")

    elif data == "donate_statuses":
        # Показываем текст со статусами
        await cb.message.edit_text(statuses_text(), reply_markup=back_to_menu_keyboard(), parse_mode="HTML")

    elif data == "donate_back":
        # Возврат в главное меню
        await cb.message.edit_text("💎 Выберите категорию:", reply_markup=donate_keyboard())

    elif data == "donate_stars":
        await cb.message.edit_text("⭐ Пополните донат через звезды внутри бота!")

    elif data == "donate_site":
        await cb.message.edit_text("🌐 Донат доступен на сайте: https://yoursite.com")
