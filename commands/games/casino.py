# commands/games/casino.py
from aiogram import Router, types, F
import random
import time
from utils.helpers import get_player, save_player, get_mention

router = Router()
COOLDOWN = 5

@router.message(F.text.lower().startswith("казино"))
async def casino_cmd(message: types.Message):
    text = message.text.lower().strip()
    user_id = message.from_user.id
    user = get_player(user_id, message.from_user.username)
    mention = get_mention(user_id, message.from_user.username)

    args = text.split()

    if len(args) == 1:
        await message.answer(f"🎰 {mention}, вы не ввели ставку.")
        return

    try:
        bet = int(args[1].replace("$", "").replace(",", ""))
    except:
        await message.answer(f"💰 {mention}, укажите сумму ставки.")
        return

    if bet <= 0:
        await message.answer(f"🚫 {mention}, ставка слишком мала.")
        return

    if user["money"] < bet:
        await message.answer(f"❌ {mention}, недостаточно средств.")
        return

    now = time.time()
    last = user.get("last_casino")
    if last and now - last < COOLDOWN:
        await message.answer(f"{mention}, играть можно каждые 5 секунд. Подождите немного 😔")
        return

    user["last_casino"] = now
    save_player(user_id, user)

    roll = random.randint(1, 100)

    if roll <= 5:
        user["money"] = 0
        # ======================
        # УВЕЛИЧИВАЕМ СЧЁТЧИК ИГР
        # ======================
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention}, все Ваши деньги сгорели! (x0) 😣")

    elif roll <= 25:
        lose = int(bet * 0.75)
        user["money"] -= lose
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention}, вы проиграли {lose}$ (x0.25) 😲")

    elif roll <= 60:
        lose = int(bet * 0.5)
        user["money"] -= lose
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention}, вы проиграли {lose}$ (x0.5) 😬")

    elif roll <= 85:
        win = bet * 2
        user["money"] += win
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention}, вы выиграли {win}$ (x2) 🤑")

    elif roll <= 97:
        win = bet * 3
        user["money"] += win
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention}, ДЖЕКПОТ {win}$ (x3) 🔥")

    else:
        win = bet * 5
        user["money"] += win
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention}, МЕГА ДЖЕКПОТ {win}$ (x5) 💎")
