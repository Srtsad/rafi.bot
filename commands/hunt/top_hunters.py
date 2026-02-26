import json
import os
import time
from datetime import datetime, timedelta
from aiogram import Router, types
from utils.helpers import get_mention  # Функция из твоего проекта

router = Router()
TOP_DB = "database/top_hunters.json"

# =========================
# СОЗДАНИЕ БАЗЫ
# =========================
if not os.path.exists("database"):
    os.makedirs("database")

if not os.path.exists(TOP_DB):
    with open(TOP_DB, "w", encoding="utf-8") as f:
        json.dump({"players": {}, "last_reset": time.time()}, f, indent=4)

def load_top():
    with open(TOP_DB, "r", encoding="utf-8") as f:
        return json.load(f)

def save_top(db):
    with open(TOP_DB, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

# =========================
# СБРОС КАЖДУЮ НЕДЕЛЮ
# =========================
def reset_weekly_top():
    db = load_top()
    last = datetime.fromtimestamp(db.get("last_reset", 0))
    now = datetime.now()
    if now - last >= timedelta(days=7):
        db["players"] = {}
        db["last_reset"] = time.time()
        save_top(db)

# =========================
# ОБНОВЛЕНИЕ ТОПА
# =========================
def add_loot_to_top(user_id: str, username: str, rarity: str, count: int = 1):
    db = load_top()
    players = db.get("players", {})
    if user_id not in players:
        players[user_id] = {
            "username": username,
            "обычная": 0,
            "редкая": 0,
            "эпик": 0,
            "мифик": 0,
            "легендарка": 0
        }
    players[user_id][rarity] += count
    db["players"] = players
    save_top(db)

# =========================
# СОЗДАНИЕ ТЕКСТА ТОПА С КЛИКАБЕЛЬНЫМИ ЮЗЕРАМИ
# =========================
def build_top_text():
    db = load_top()
    players = db.get("players", {})

    def score(p):
        return p["редкая"]*1 + p["эпик"]*3 + p["мифик"]*5 + p["легендарка"]*7

    top_list = sorted(players.items(), key=lambda x: score(x[1]), reverse=True)[:10]

    text = "🏆 <b>ТОП ОХОТНИКОВ</b>\n━━━━━━━━━━━━━━\n"
    for i, (user_id, p) in enumerate(top_list, 1):
        mention = get_mention(int(user_id), p.get("username", "Игрок"))
        text += (
            f"{i}️⃣ {mention} — 🐺 Редкая ×{p['редкая']} | "
            f"💎 Эпическая ×{p['эпик']} | 💠 Мифическая ×{p['мифик']} | "
            f"🌟 Легендарная ×{p['легендарка']}\n"
        )
    if not top_list:
        text += "Пока нет игроков\n"
    text += "━━━━━━━━━━━━━━\n💡 Совет:\nЧем больше редких и эпических трофеев выбьет игрок, тем выше он в топе\n"
    text += "Легендарная и мифическая добыча дают максимальный прирост очков"
    return text

# =========================
# КОМАНДА ТОП
# =========================
@router.message(lambda m: m.text.lower() == "охота топ")
async def top_hunters_command(message: types.Message):
    reset_weekly_top()
    text = build_top_text()
    await message.answer(text, parse_mode="HTML")
