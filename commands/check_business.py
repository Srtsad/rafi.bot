from aiogram import Router, types
from utils.helpers import get_mention

router = Router()

# ===== Команда "Чек бизнес" =====
@router.message(lambda m: m.text and m.text.strip().lower() == "все бизнесы")
async def cmd_check_business(message: types.Message):
    user = message.from_user
    mention = get_mention(user.id, user.first_name or "Игрок")

    text = (
        f"━━━━━━━━━━━━━━\n"
        f"💼 <b>ГОРОДСКИЕ БИЗНЕСЫ</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🥪 Ларёк с продуктами — 5.000.000$\n"
        f"💨 Вейп-шоп «Пароход» — 8.000.000$\n"
        f"🛒 Магазин 24/7 — 12.000.000$\n"
        f"🛡 Охранная компания «Затвор» — 20.000.000$\n"
        f"🎶 Ночной клуб «Miami» — 50.000.000$\n"
        f"━━━━━━━━━━━━━━\n"
        f"💎 <b>ПРЕМИУМ-КОМПЛЕКСЫ</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"💃 Стрип-клуб «Euphoria» — 100.000.000$\n"
        f"🚘 Автосалон «DriveX» — 400.000.000$\n"
        f"🛥 Яхт-клуб «Neptune» — 500.000.000$\n"
        f"🎰 Казино «Fortune» — 777.777.777$\n"
        f"━━━━━━━━━━━━━━\n"
        f"🏢 <b>КОРПОРАЦИИ И ХОЛДИНГИ</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🏦 Инвестиционный банк «Capital» — 1.000.000.000$\n"
        f"🧪 Лаборатория синтеза «Alchemica» — 3.500.000.000$\n"
        f"🛰 Космопорт «Orion» — 6.000.000.000$\n"
        f"🏗 Строительная корпорация «Titan» — 9.000.000.000$\n"
        f"🧠 IT-холдинг «NeuroTech» — 15.000.000.000$\n"
        f"🌌 Квантовая станция «Eternium» — 40.000.000.000$\n"
        f"━━━━━━━━━━━━━━\n"
        f"👑 <b>VIP-ПРЕДПРИЯТИЯ</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🚔 Наркоконтроль «Shadow» — 20.000.000.000$\n"
        f"🔒 Ограниченном количестве всего 3шт\n"
        f"━━━━━━━━━━━━━━"
    )

    await message.answer(text, parse_mode="HTML")
