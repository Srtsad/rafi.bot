# commands/forbes.py
from aiogram import Router, types
from utils.helpers import _load_players, get_mention

router = Router()

@router.message(lambda message: message.text and message.text.lower() in ["форбс", "топ денег"])
async def forbes_cmd(message: types.Message):
    players = _load_players()

    # составляем список игроков с деньгами
    rich_list = [(p.get("money", 0), uid) for uid, p in players.items() if p.get("money", 0) > 0]

    if not rich_list:
        await message.answer("💤 Нет игроков с деньгами")
        return

    # сортировка по убыванию денег
    rich_list.sort(reverse=True)

    # формируем текст
    txt = "💰 <b>ТОП 10 FORBES</b>\n\n"
    for i, (money, uid) in enumerate(rich_list[:10], 1):
        txt += f"{i}. {get_mention(int(uid))} — {money:,}$\n"

    await message.answer(txt, parse_mode="HTML")
