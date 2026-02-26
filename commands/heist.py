from aiogram import Router, types
from utils.helpers import get_player, try_heist

router = Router()

@router.message(lambda m: m.text and m.text.lower() == "ограбить мэрию")
async def heist_cmd(message: types.Message):
    user = message.from_user
    player = get_player(user.id, user.first_name)

    name = player.get("nickname") or "Игрок"
    mention = f'<a href="tg://user?id={user.id}">{name}</a>'

    result, reward = try_heist(user.id)

    if result == "cooldown":
        await message.answer(
            f"🚨 {mention}, вы уже пытались ограбить казну сегодня!\n"
            f"🏃 Бегите, полиция уже выехала!",
            parse_mode="HTML"
        )
        return

    if result == "fail":
        await message.answer(
            f"❎ {mention}, к сожалению вам не удалось ограбить казну.\n"
            f"👮 Сигнализация сработала слишком быстро!",
            parse_mode="HTML"
        )
        return

    await message.answer(
        f"💰 <b>УДАЧНОЕ ОГРАБЛЕНИЕ!</b>\n\n"
        f"🏛 {mention} ограбил(-а) казну мэрии\n"
        f"🤑 Добыча: <b>{reward:,}$</b>",
        parse_mode="HTML"
    )
