from aiogram import Router, types
from utils.helpers import _load_players, get_mention

router = Router()

# Команда: казна / Казна
@router.message(lambda m: m.text and m.text.strip().lower() == "казна")
async def cmd_kazna(message: types.Message):
    players = _load_players()

    total_money = 0
    total_btc = 0.0

    for player in players.values():
        total_money += player.get("money", 0)
        total_money += player.get("bank", 0)
        total_money += player.get("biz_account", 0)
        total_btc += player.get("btc", 0.0)

    # Форматирование
    money_fmt = f"{total_money:,}".replace(",", ".")
    btc_fmt = f"{total_btc:,.8f}".replace(",", ".")

    mention = get_mention(
        message.from_user.id,
        message.from_user.first_name
    )

    text = (
        f"🏛 <b>Казна государства</b>\n\n"
        f"👤 Запросил: {mention}\n\n"
        f"💰 <b>Общий капитал:</b> {money_fmt}$\n"
        f"💽 <b>Всего BTC:</b> {btc_fmt}฿\n\n"
        f"📊 Данные собраны со всех счетов игроков"
    )

    await message.answer(text, parse_mode="HTML")
