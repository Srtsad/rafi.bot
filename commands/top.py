# commands/top.py
from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from utils.helpers import _load_players, get_mention
import json, os, time
from datetime import datetime, timedelta

router = Router()
TOP_DB = "database/top_hunters.json"

os.makedirs("database", exist_ok=True)
if not os.path.exists(TOP_DB):
    with open(TOP_DB, "w", encoding="utf-8") as f:
        json.dump({"players": {}, "last_reset": time.time()}, f, indent=4)

def load_top():
    with open(TOP_DB, "r", encoding="utf-8") as f:
        return json.load(f)

def save_top(db):
    with open(TOP_DB, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def reset_weekly_top():
    db = load_top()
    last = datetime.fromtimestamp(db.get("last_reset", 0))
    now = datetime.now()
    if now - last >= timedelta(days=7):
        db["players"] = {}
        db["last_reset"] = time.time()
        save_top(db)

def build_hunters_top():
    db = load_top()
    players = db.get("players", {})

    def score(p):
        return p["редкая"]*1 + p["эпик"]*3 + p["мифик"]*5 + p["легендарка"]*7

    top_list = sorted(players.items(), key=lambda x: score(x[1]), reverse=True)[:10]
    text = "🏆 <b>ТОП ОХОТНИКОВ</b>\n━━━━━━━━━━━━━━\n"
    for i, (uid, p) in enumerate(top_list, 1):
        mention = get_mention(int(uid), p.get("username", "Игрок"))
        text += (
            f"{i}️⃣ {mention} — 🐺 Редкая ×{p['редкая']} | "
            f"💎 Эпическая ×{p['эпик']} | 💠 Мифическая ×{p['мифик']} | "
            f"🌟 Легендарная ×{p['легендарка']}\n"
        )
    if not top_list:
        text += "Пока нет игроков\n"
    return text

def build_forbes_top():
    players = _load_players()
    rich_list = [(p.get("money", 0), uid) for uid, p in players.items() if p.get("money", 0) > 0]
    if not rich_list:
        return "💤 Нет игроков с деньгами"
    rich_list.sort(reverse=True)
    text = "💰 <b>ТОП 10 FORBES</b>\n\n"
    for i, (money, uid) in enumerate(rich_list[:10], 1):
        text += f"{i}. {get_mention(int(uid))} — {money:,}$\n"
    return text

def build_games_top():
    players = _load_players()
    played_players = [
        (p["user_id"], p.get("nickname") or p.get("username") or f"Игрок {p['user_id']}", p.get("games_played", 0))
        for p in players.values() if p.get("games_played", 0) > 0
    ]
    if not played_players:
        return "🎮 Топ игроков пока пуст 😔"
    top_players = sorted(played_players, key=lambda x: x[2], reverse=True)[:10]
    text = "🏆 <b>ТОП 10 ИГРОКОВ ПО КОЛИЧЕСТВУ ИГР</b> 🏆\n\n"
    for i, (uid, name, games) in enumerate(top_players, start=1):
        mention = f'<a href="tg://user?id={uid}">{name}</a>'
        text += f"{i}. {mention} — 🎲 {games} игр\n"
    return text

def build_duel_top():
    from commands.games.duel import load_json, STATS_FILE, get_mention, get_reset_minutes, check_reset
    check_reset()
    stats = load_json(STATS_FILE)
    stats.pop("_reset_time", None)
    if not stats:
        return "⚔️ Нет побед в дуэлях"
    top = sorted(stats.items(), key=lambda x:x[1], reverse=True)[:10]
    txt="🏆 <b>ТОП ДУЭЛЯНТОВ</b>\n━━━━━━━━━━━━━━\n"
    for i,(uid,w) in enumerate(top,1):
        txt+=f"{i}. {get_mention(int(uid))} — {w}\n"
    txt += f"\n⏳ До сброса: {get_reset_minutes()} мин"
    return txt

def top_keyboard():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏹 Топ охоты", callback_data="top_hunters"),
                InlineKeyboardButton(text="🎮 Топ игр", callback_data="top_games")
            ],
            [
                InlineKeyboardButton(text="💰 Форбс", callback_data="top_forbes"),
                InlineKeyboardButton(text="⚔️ Топ дуэлей", callback_data="top_duels")
            ]
        ]
    )
    return kb

@router.message(lambda m: m.text.lower() == "топы")
async def show_top_menu(message: types.Message):
    await message.answer("Выберите топ:", reply_markup=top_keyboard())

@router.callback_query(lambda c: c.data.startswith("top_"))
async def callback_top(cb: CallbackQuery):
    data = cb.data
    text = ""
    if data == "top_hunters":
        reset_weekly_top()
        text = build_hunters_top()
    elif data == "top_games":
        text = build_games_top()
    elif data == "top_forbes":
        text = build_forbes_top()
    elif data == "top_duels":
        text = build_duel_top()
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=top_keyboard())
    await cb.answer()
