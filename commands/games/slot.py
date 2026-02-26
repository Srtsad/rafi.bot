import asyncio
import random
import time
from aiogram import Router, types, F
from utils.helpers import get_player, save_player, get_mention

router = Router()
COOLDOWN = 5  # секунда между спинами

@router.message(F.text.lower().startswith("спин"))
async def slot_cmd(message: types.Message):
    text = message.text.lower().strip()
    user_id = message.from_user.id
    user = get_player(user_id, message.from_user.username)
    mention = get_mention(user_id, message.from_user.username)

    args = text.split()
    if len(args) < 2:
        await message.answer(f"🎰 {mention}, укажите ставку!")
        return

    # проверяем ставку
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
    last = user.get("last_slot")
    if last and now - last < COOLDOWN:
        await message.answer(f"{mention}, играть можно каждые {COOLDOWN} секунд. Подождите немного ⏳")
        return

    user["last_slot"] = now
    save_player(user_id, user)

    # 🎰 Отправляем игровой автомат (анимация)
    slot_msg = await message.answer_dice(emoji="🎰")
    await asyncio.sleep(3)  # ждем анимацию

    # результат спина: случайное число от 1 до 100
    roll = random.randint(1, 100)

    # шансы на выпадение
    if roll <= 5:  # сгорело всё
        user["money"] = 0
        # ======================
        # УВЕЛИЧИВАЕМ СЧЁТЧИК ИГР
        # ======================
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention}, все Ваши деньги сгорели! (x0) 😣")
        return

    elif roll <= 25:
        lose = int(bet * 0.75)
        user["money"] -= lose
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention}, вы проиграли {lose}$ (x0.25) 😲")
        return

    elif roll <= 60:
        lose = int(bet * 0.5)
        user["money"] -= lose
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention}, вы проиграли {lose}$ (x0.5) 😬")
        return

    elif roll <= 85:
        win = bet * 2
        user["money"] += win
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention}, вы выиграли {win}$ (x2) 🤑")
        return

    elif roll <= 97:
        win = bet * 3
        user["money"] += win
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention}, ДЖЕКПОТ {win}$ (x3) 🔥")
        return

    else:
        win = bet * 5
        user["money"] += win
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(f"{mention}, МЕГА ДЖЕКПОТ {win}$ (x5) 💎")
        return
