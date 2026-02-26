import asyncio
import random
import time
from aiogram import Router, types, F
from utils.helpers import get_player, save_player, get_mention

router = Router()
COOLDOWN = 5  # секунда между бросками

@router.message(F.text.lower().startswith("баскетбол"))
async def basketball_cmd(message: types.Message):
    text = message.text.lower().strip()
    user_id = message.from_user.id
    user = get_player(user_id, message.from_user.username)
    mention = get_mention(user_id, message.from_user.username)

    args = text.split()
    if len(args) < 2:
        await message.answer(f"🏀 {mention}, укажите ставку!")
        return

    # проверка ставки
    try:
        bet = int(args[1].replace("$", "").replace(",", ""))
    except:
        await message.answer(f"💰 {mention}, ставка должна быть числом!")
        return

    if bet <= 0:
        await message.answer(f"🚫 {mention}, ставка слишком мала.")
        return

    if user["money"] < bet:
        await message.answer(f"❌ {mention}, недостаточно средств.")
        return

    # проверка cooldown
    now = time.time()
    last = user.get("last_basketball")
    if last and now - last < COOLDOWN:
        await message.answer(f"{mention}, играть можно каждые {COOLDOWN} секунд. Подождите немного ⏳")
        return

    user["last_basketball"] = now
    save_player(user_id, user)

    # 🏀 Отправляем эмодзи броска (анимация)
    ball_msg = await message.answer_dice(emoji="🏀")
    await asyncio.sleep(3)  # ждем анимацию

    # результат броска: value от 1 до 6 (по API Telegram)
    result = ball_msg.dice.value

    # создаем шансы
    if result <= 1:
        # полный промах
        lose = bet
        user["money"] -= lose
        # ======================
        # УВЕЛИЧИВАЕМ СЧЁТЧИК ИГР
        # ======================
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention} | К сожалению, промах! ❌\n-{lose}$")
        return

    elif result <= 3:
        # частичный успех
        lose = int(bet * 0.5)
        user["money"] -= lose
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention} | Попытка неудачна 😬\n-{lose}$")
        return

    elif result <= 5:
        # удачный бросок
        win = bet * 2
        user["money"] += win
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention} | Отличный бросок! 🏀 +{win}$")
        return

    else:
        # супер-бросок
        win = bet * 3
        user["money"] += win
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention} | Супер-бросок! 🔥 +{win}$")
        return
