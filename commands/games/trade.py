from aiogram import Router, types
import random, time
from utils.helpers import get_player, save_player, get_mention

router = Router()
COOLDOWN = 5  # секунд между играми
EMOJI_UP = "📈"
EMOJI_DOWN = "📉"

@router.message(lambda message: message.text and message.text.lower().startswith("трейд"))
async def trade_cmd(message: types.Message):
    user_id = message.from_user.id
    user = get_player(user_id, message.from_user.username)
    mention = get_mention(user_id, message.from_user.username)

    args = message.text.split()
    if len(args) < 3:
        await message.answer(f"💹 {mention}, пример: Трейд [вверх/вниз] [ставка]")
        return

    direction = args[1].lower()
    if direction not in ["вверх", "вниз"]:
        await message.answer(f"❌ {mention}, выберите 'вверх' или 'вниз'.")
        return

    try:
        bet = int(args[2].replace("$", "").replace(",", ""))
    except:
        await message.answer(f"💰 {mention}, укажите сумму ставки числом.")
        return

    if bet <= 0:
        await message.answer(f"🚫 {mention}, ставка слишком мала.")
        return
    if user["money"] < bet:
        await message.answer(f"❌ {mention}, недостаточно средств.")
        return

    now = time.time()
    last = user.get("last_trade")
    if last and now - last < COOLDOWN:
        await message.answer(f"{mention}, играть можно каждые 5 секунд. Подождите немного 😔")
        return
    user["last_trade"] = now

    # Случайное движение рынка
    result = random.choice(["вверх", "вниз"])
    emoji_result = EMOJI_UP if result == "вверх" else EMOJI_DOWN

    # Случайный процент изменения курса от 1% до 99%
    percent_change = random.randint(1, 99)

    # Рассчёт выигрыша или проигрыша
    if direction == result:
        win_amount = int(bet * (percent_change / 100))
        user["money"] += win_amount
        await message.answer(f"{mention}, {emoji_result} курс пошёл {result} на {percent_change}%\n🤑 Ваш выигрыш составил {win_amount}$")
    else:
        lose_amount = int(bet * (percent_change / 100))
        user["money"] -= lose_amount
        await message.answer(f"{mention}, {emoji_result} курс пошёл {result} на {percent_change}%\n❌ Ваш проигрыш составил {lose_amount}$")

    # ======================
    # УВЕЛИЧИВАЕМ СЧЁТЧИК ИГР
    # ======================
    user["games_played"] = user.get("games_played", 0) + 1

    save_player(user_id, user)
