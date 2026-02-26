# commands/mine/refill_energy.py
from aiogram import Router, types
from utils.helpers import get_player, save_player, ENERGY_MAX

router = Router()

# Команда для полного пополнения энергии
@router.message(lambda m: m.text and m.text.lower() in ["пополнить энергию", "энергия полная"])
async def refill_energy(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)

    if player["energy"] >= ENERGY_MAX:
        await message.answer("⚡ У тебя уже полная энергия!")
        return

    player["energy"] = ENERGY_MAX
    player["last_energy_tick"] = None  # сброс таймера восстановления
    save_player(user_id, player)

    await message.answer(f"⚡ Энергия восстановлена до {ENERGY_MAX}/{ENERGY_MAX}!\nТеперь можно копать и играть без ограничений.")
