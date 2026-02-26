from aiogram import Router, types
from utils.helpers import get_player, save_player, ENERGY_MAX, ENERGY_INTERVAL, ENERGY_TICK
import time

router = Router()

@router.message(lambda m: m.text and m.text.lower() == "энергия")
async def cmd_energy(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id)

    now = time.time()

    # безопасно берём last_energy_tick
    last_tick = player.get("last_energy_tick")
    if not isinstance(last_tick, (int, float)):
        last_tick = now
        player["last_energy_tick"] = now
        save_player(user_id, player)

    # считаем сколько тиков прошло
    elapsed = now - last_tick
    ticks = int(elapsed // ENERGY_INTERVAL)

    if ticks > 0:
        # добавляем энергию, не больше максимума
        player["energy"] = min(ENERGY_MAX, player.get("energy", 0) + ticks * ENERGY_TICK)
        # обновляем последний тик
        player["last_energy_tick"] = last_tick + ticks * ENERGY_INTERVAL
        save_player(user_id, player)

    # время до следующего восстановления
    remaining = ENERGY_INTERVAL - ((now - player.get("last_energy_tick", now)) % ENERGY_INTERVAL)
    minutes, seconds = divmod(int(remaining), 60)

    if player["energy"] >= ENERGY_MAX:
        text = f"⚡ ЭНЕРГИЯ ПОЛНАЯ\n\n{player['energy']} / {ENERGY_MAX}"
    else:
        text = (
            f"⚡ ТВОЯ ЭНЕРГИЯ\n\n"
            f"{player['energy']} / {ENERGY_MAX}\n"
            f"+{ENERGY_TICK} каждые {ENERGY_INTERVAL//60} минут\n\n"
            f"⏳ До следующего восстановления: {minutes:02d}:{seconds:02d}"
        )

    await message.answer(text)
