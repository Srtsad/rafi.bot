from aiogram import Router, types
from datetime import datetime, timedelta
from utils.helpers import get_player, save_player, get_mention

router = Router()

PERCENT = 0.06  # 6%

def can_do(last_time):
    if not last_time:
        return True
    return datetime.utcnow() - datetime.fromisoformat(last_time) >= timedelta(days=1)

@router.message(lambda m: m.text and m.text.lower().startswith("депозит"))
async def deposit_cmd(message: types.Message):
    args = message.text.lower().split()
    player = get_player(message.from_user.id, message.from_user.first_name)

    if len(args) < 3:
        return await message.answer("❌ Используй: Депозит положить/снять сумма/всё")

    action = args[1]
    value = args[2]

    if action == "положить":
        if not can_do(player["last_deposit_put"]):
            return await message.answer("⏳ Депозит можно пополнять раз в сутки")

        amount = player["bank"] if value == "всё" else int(value)
        if player["bank"] < amount or amount <= 0:
            return await message.answer("❌ Недостаточно денег в банке")

        player["bank"] -= amount
        player["deposit"] += amount
        player["last_deposit_put"] = datetime.utcnow().isoformat()
        save_player(message.from_user.id, player)
        return await message.answer(f"💵 Ты положил в депозит {amount}$")

    elif action == "снять":
        if not can_do(player["last_deposit_take"]):
            return await message.answer("⏳ Депозит можно снимать раз в сутки")

        amount = player["deposit"] if value == "всё" else int(value)
        if player["deposit"] < amount or amount <= 0:
            return await message.answer("❌ Недостаточно средств в депозите")

        profit = int(amount * PERCENT)
        total = amount + profit

        player["deposit"] -= amount
        player["bank"] += total
        player["last_deposit_take"] = datetime.utcnow().isoformat()
        save_player(message.from_user.id, player)

        return await message.answer(
            f"💎 Ты снял депозит\n"
            f"💵 Сумма: {amount}$\n"
            f"〽 Проценты: +{profit}$"
        )

    else:
        return await message.answer("❌ Действие: положить или снять")
