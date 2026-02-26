from aiogram import Router, types
from utils.helpers import get_player, get_mention

router = Router()

# Команда "б" или "баланс"
@router.message(lambda m: m.text and m.text.lower() in ["б", "баланс"])
async def cmd_balance(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name

    player = get_player(user_id, username)

    mention = get_mention(user_id, username)

    # деньги
    money = f"{player.get('money', 0):,}".replace(",", ".")

    # бизнес счет (ОБЩИЙ)
    biz_account = f"{player.get('biz_account', 0):,}".replace(",", ".")

    # банк
    bank = f"{player.get('bank', 0):,}".replace(",", ".")

    # биткоины
    btc = player.get("btc", 0)

    text = (
        f"👤 Ник: {mention}\n"
        f"💰 Деньги: {money}$\n"
        f"💳 Бизнес счёт: {biz_account}$\n"
        f"🏦 Банк: {bank}$\n"
        f"💽 Биткоины: {btc}฿"
    )

    await message.answer(text, parse_mode="HTML")
