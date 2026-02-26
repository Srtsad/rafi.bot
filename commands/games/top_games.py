# commands/games/top_games.py
from aiogram import Router, types
from utils.helpers import _load_players

router = Router()

@router.message(lambda m: m.text and m.text.lower() in ["топ игры", "топ игр"])
async def top_games(message: types.Message):
    players = _load_players()

    # Берём только тех, кто сыграл хотя бы одну игру
    played_players = [(p["user_id"], p.get("nickname") or p.get("username") or f"Игрок {p['user_id']}", p.get("games_played", 0))
                      for p in players.values() if p.get("games_played", 0) > 0]

    if not played_players:
        await message.answer("🎮 Топ игроков пока пуст 😔")
        return

    # Сортировка по количеству сыгранных игр
    top_players = sorted(played_players, key=lambda x: x[2], reverse=True)[:10]

    text = "🏆 **ТОП 10 ИГРОКОВ ПО КОЛИЧЕСТВУ ИГР** 🏆\n\n"
    for i, (uid, name, games) in enumerate(top_players, start=1):
        mention = f'<a href="tg://user?id={uid}">{name}</a>'
        text += f"{i}. {mention} — 🎲 **{games} игр**\n"

    text += "\n🔥 Продолжайте играть, чтобы подняться в рейтинге!"

    await message.answer(text, parse_mode="HTML")
