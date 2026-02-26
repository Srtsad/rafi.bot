# commands/games/dice.py
import asyncio
import time
from aiogram import Router, types, F
from utils.helpers import get_player, save_player, get_mention

router = Router()
COOLDOWN = 3

@router.message(F.text.lower().startswith("кубик"))
async def dice_cmd(message: types.Message):
    text = message.text.lower().strip()
    user_id = message.from_user.id
    user = get_player(user_id, message.from_user.username)
    mention = get_mention(user_id, message.from_user.username)

    args = text.split()
    if len(args) < 2:
        await message.answer(f"{mention} | укажите число от 1 до 6 🎲")
        return
    if len(args) < 3:
        await message.answer(f"{mention} | укажите ставку 💰")
        return

    try:
        number = int(args[1])
        bet = int(args[2].replace("$", "").replace(",", ""))
    except:
        await message.answer(f"{mention} | число и ставка должны быть числами!")
        return

    if number < 1 or number > 6:
        await message.answer(f"{mention} | можно выбрать число только от 1 до 6 🎲")
        return
    if bet <= 0:
        await message.answer(f"{mention} | ставка слишком мала 🚫")
        return
    if user["money"] < bet:
        await message.answer(f"{mention} | недостаточно средств ❌")
        return

    now = time.time()
    last = user.get("last_dice")
    if last and now - last < COOLDOWN:
        await message.answer(f"{mention} | подождите пару секунд ⏳")
        return

    user["last_dice"] = now
    save_player(user_id, user)

    # 🎲 Отправляем кубик
    dice_msg = await message.answer_dice(emoji="🎲")
    await asyncio.sleep(3)  # ждем анимацию кубика

    result = dice_msg.dice.value

    if result != number:
        user["money"] -= bet
        # ======================
        # УВЕЛИЧИВАЕМ СЧЁТЧИК ИГР
        # ======================
        user["games_played"] = user.get("games_played", 0) + 1
        save_player(user_id, user)
        await message.answer(
            f"{mention} | К сожалению вы не угадали число! 🎲\n"
            f"Выпало: {result}\n"
            f"-{bet}$"
        )
        return

    win = bet * 2
    user["money"] += win
    user["games_played"] = user.get("games_played", 0) + 1
    save_player(user_id, user)
    await message.answer(
        f"{mention} | ВЫ УГАДАЛИ ЧИСЛО {result}! 🎉\n"
        f"+{win}$"
    )
