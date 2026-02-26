from aiogram import Router
from aiogram.types import CallbackQuery
from keyboards.menu_keyboards import menu_categories, back_button

router = Router()

CHAT_LINK = "https://t.me/RafiChatfirst"
SUPPORT_LINK = "https://t.me/RafiSupportHelp"


def get_click_name(user):
    # если ник не стоит → просто Игрок (кликабельный)
    name = user.first_name if user.first_name else "Игрок"
    return f'<a href="tg://user?id={user.id}">{name}</a>'


# ===================== ИГРЫ =====================
@router.callback_query(lambda c: c.data == "cat_games")
async def games_menu(call: CallbackQuery):
    user = call.from_user
    name = get_click_name(user)

    text = (
        f"👤 {name} | игровые команды:\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎲 Топ игры - показывает топ 10\n"
        f"━━━━━━━━━━━━━━\n"
        f"🚀 <b>Игры:</b>\n"
        f"🎮 Спин [ставка]\n"
        f"🎲 Кубик [число] [ставка]\n"
        f"🏀 Баскетбол [ставка]\n"
        f"🎯 Дартс [ставка]\n"
        f"🎳 Боулинг [ставка]\n"
        f"📉 Трейд [вверх/вниз] [ставка]\n"
        f"🎰 Казино [ставка]\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎭 <b>Развлечения:</b>\n"
        f"🔮 Шар [фраза]\n"
        f"💬 Выбери [фраза] или [фраза2]\n"
        f"📊 Инфа [фраза]\n"
        f"━━━━━━━━━━━━━━\n"
        f"🔫 <b>Дуэли:</b>\n"
        f"🤴 Топ дуэлей\n"
        f"🔫 Дуэль [ответ/юз]\n"
        f"💰 Дуэль ставка [сумма]\n"
        f"💣 Отменить дуэль\n"
        f"🏳️ Сдаться\n"
        f"━━━━━━━━━━━━━━\n"
        f"💒 <b>Браки:</b>\n"
        f"💖 Свадьба [ID]\n"
        f"💔 Развод\n"
        f"💌 Мой брак\n"
        f"━━━━━━━━━━━━━━"
    )

    await call.message.edit_text(text, reply_markup=back_button(), disable_web_page_preview=True)
    await call.answer()


# ===================== РАЗВЛЕКАТЕЛЬНОЕ =====================
@router.callback_query(lambda c: c.data == "cat_fun")
async def fun_menu(call: CallbackQuery):
    user = call.from_user
    name = get_click_name(user)

    text = (
        f"👤 {name}, развлекательные команды:\n"
        f"━━━━━━━━━━━━━━\n"
        f"🏢 Аукцион ⚠️\n"
        f"💵 Купить - [Название Бизнеса] - [Сумма] ⚠️\n"
        f"💼 Форбс\n"
        f"━━━━━━━━━━━━━━\n"
        f"⛏ <b>Добыча/Работы:</b>\n"
        f"🪨 Шахта\n"
        f"📊 Курс руды\n"
        f"⛏ Копать руду\n"
        f"🚚 Купить/продать [руда] [кол-во]\n"
        f"━━━━━━━━━━━━━━\n"
        f"📦 <b>Кейсы:</b>\n"
        f"🛒 Купить кейс [номер] [кол-во]⚠️\n"
        f"🔐 Открыть кейс [номер] [кол-во]⚠️\n"
        f"━━━━━━━━━━━━━━\n"
        f"🗄 <b>Бизнес:</b>\n"
        f"💼 Купить - [назв.биз]\n"
        f"💰 Мой - [назв.биз]\n"
        f"💸 Продать - [назв.биз]\n"
        f"🏢 Все бизнесы\n"
        f"💳 Вывести [сумма/всё]\n"
        f"━━━━━━━━━━━━━━\n"
        f"🧰 <b>Майнинг ферма:</b> ⚠️\n"
        f"🔋 Моя ферма/ферма\n"
        f"━━━━━━━━━━━━━━\n"
        f"🌿 <b>Ферма:</b> ⚠️\n"
        f"🪧 Моя ферма/ферма\n"
        f"💦 Ферма полить\n"
        f"⚗  Создать зелье [номер]\n"
        f"━━━━━━━━━━━━━━\n"
        f"🪶 <b>Охота:</b>\n"
        f"🎯 Охота помощь - подсказки\n"
        f"👨‍🌾 Охота - меню охотника\n"
        f"🔫 Стрелять - выстрел с ружья\n"
        f"📦 Купить - [ Предмет ] в лавке\n"
        f"🦣 Курс добычи - цены на продажу\n"
        f"━━━━━━━━━━━━━━\n"
        f"⚠️ <b>временно недоступные функции</b>"
    )

    await call.message.edit_text(text, reply_markup=back_button(), disable_web_page_preview=True)
    await call.answer()


# ===================== ОСНОВНОЕ =====================
@router.callback_query(lambda c: c.data == "cat_main")
async def main_menu(call: CallbackQuery):
    user = call.from_user
    name = get_click_name(user)

    text = (
        f"👤 {name} | Основные команды\n"
        f"━━━━━━━━━━━━━━\n"
        f"💡 Профиль и статус\n"
        f"━━━━━━━━━━━━━━\n"
        f"🏆 Топы - Показывает список лучших игроков\n"
        f"🏦 Донат\n"
        f"📒 Профиль\n"
        f"👨 Мой ник\n"
        f"💢 Сменить ник [новый]\n"
        f"🏆 Мой статус\n"
        f"🔱 Статусы\n"
        f"👑 Рейтинг\n"
        f"👑 Продать рейтинг\n"
        f"━━━━━━━━━━━━━━\n"
        f"⚡ Ресурсы и бонусы\n"
        f"━━━━━━━━━━━━━━\n"
        f"⚡ Энергия\n"
        f"💫 Мой лимит\n"
        f"💈 Бонус\n"
        f"━━━━━━━━━━━━━━\n"
        f"💸 Б/Баланс\n"
        f"💷 Казна\n"
        f"💰 Банк [положить/снять] [сумма]\n"
        f"💵 Депозит [положить/снять] [сумма]\n"
        f"🤝 Дать [сумма]\n"
        f"━━━━━━━━━━━━━━\n"
        f"🧾 Владения Игрока\n"
        f"━━━━━━━━━━━━━━\n"
        f"🚗 Машины\n"
        f"📱 Телефоны\n"
        f"✈ Самолёты\n"
        f"🛥 Яхты\n"
        f"🚁 Вертолёты\n"
        f"🏠 Дома\n"
        f"📦 Инвентарь\n"
        f"🧾 Имущество\n"
        f"━━━━━━━━━━━━━━\n"
        f"🪙 Биткоин\n"
        f"🌐 Биткоин курс\n"
        f"🌐 Купить/продать Биткоин\n"
        f"━━━━━━━━━━━━━━\n"
        f"🏢 Ограбить мэрию\n"
        f"━━━━━━━━━━━━━━\n"
        f"⚖ РП команды\n"
        f"💭 <a href='{CHAT_LINK}'>Беседа</a>\n"
        f"━━━━━━━━━━━━━━"
    )

    await call.message.edit_text(text, reply_markup=back_button(), disable_web_page_preview=True)
    await call.answer()


# ===================== КЛАНЫ =====================
@router.callback_query(lambda c: c.data == "cat_clans")
async def clans_menu(call: CallbackQuery):
    user = call.from_user
    name = get_click_name(user)

    text = (
        f"👤 {name}, клановые команды:\n"
        f"━━━━━━━━━━━━━━\n"
        f"💡 Мой клан\n"
        f"🏆 Клан топ\n"
        f"Клан пригласить [ID]\n"
        f"🙋‍♂️ Клан вступить [ID]\n"
        f"📛 Клан исключить [ID]\n"
        f"🚷 Клан выйти\n"
        f"💰 Клан казна\n"
        f"💵 Клан казна [сумма]\n"
        f"━━━━━━━━━━━━━━\n"
        f"⚙ Клан создать [название] — 250.000.000.000$\n"
        f"━━━━━━━━━━━━━━\n"
        f"⤴ Клан повысить [ID]\n"
        f"⤵ Клан понизить [ID]\n"
        f"👑 Клан передать [ID]\n"
        f"📛 Клан удалить\n"
        f"━━━━━━━━━━━━━━"
    )

    await call.message.edit_text(text, reply_markup=back_button(), disable_web_page_preview=True)
    await call.answer()


# ===================== НАЗАД =====================
@router.callback_query(lambda c: c.data == "back_to_menu")
async def back(call: CallbackQuery):
    text = (
        f"👋 <b>Выбери категорию:</b>\n\n"

        f"━━━━━━━━━━━━━━━\n"
        f"🧩 <b>Основное</b>\n"
        f"🎮 <b>Игры</b>\n"
        f"🎭 <b>Развлекательное</b>\n"
        f"🏰 <b>Кланы</b>\n"
        f"━━━━━━━━━━━━━━━\n\n"

        f"💬 <a href='https://t.me/RafiChatfirst'><b>Общая беседа №1</b></a> — место для всех игроков\n"
        f"🆘 <a href='https://t.me/RafiSupportHelp'><b>Support</b></a> — помощь и вопросы"
    )

    await call.message.edit_text(
        text,
        reply_markup=menu_categories(),
        disable_web_page_preview=True
    )
    await call.answer()

