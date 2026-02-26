from aiogram import Router, types
from utils.helpers import get_player, change_nick

router = Router()


@router.message(lambda m: m.text and m.text.lower() in ["ник", "мой ник"])
async def my_nick(message: types.Message):
    user = message.from_user
    player = get_player(user.id, user.first_name)

    display_name = player.get("nickname") or "Игрок"
    mention = f'<a href="tg://user?id={user.id}">{display_name}</a>'

    await message.answer(
        f'🗂 Ваш ник — «{mention}»',
        parse_mode="HTML"
    )


@router.message(lambda m: m.text and m.text.lower().startswith("сменить ник"))
async def set_nick(message: types.Message):
    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        await message.answer("💢 Сменить ник [новый ник]")
        return

    new_nick = parts[2]

    if len(new_nick) < 5:
        await message.answer(f"❌ {new_nick}, ваш ник не может быть короче 5 символов 😞")
        return

    ok, error = change_nick(message.from_user.id, new_nick)
    if not ok:
        await message.answer(error)
        return

    await message.answer(f"✅ Ваш ник изменён на «{new_nick}»")
