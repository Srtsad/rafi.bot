import json
import os
import time
import random
import logging
import requests
from datetime import datetime, timedelta

DATA_FILE = "database/players.json"
LOG_DIR = "logs"
LOG_FILE = f"{LOG_DIR}/system.log"

# ⚡ Энергия
ENERGY_MAX = 100
ENERGY_TICK = 5
ENERGY_INTERVAL = 600  # 5 минут

# ⚡ Удаление неактивных (4 месяца)
INACTIVE_DAYS = 120


# ======================
# ЛОГИРОВАНИЕ (ИСПРАВЛЕНО)
# ======================

os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("game_logger")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# очищаем возможные старые handlers (чтобы не конфликтовало с aiogram)
if logger.hasHandlers():
    logger.handlers.clear()

logger.addHandler(file_handler)
logger.addHandler(console_handler)


# ======================
# ВНУТРЕННИЕ ФУНКЦИИ
# ======================

def _load_players():
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка чтения базы: {e}")
        return {}


def _save_players(players: dict):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(players, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Ошибка сохранения базы: {e}")


# ======================
# УДАЛЕНИЕ НЕАКТИВНЫХ
# ======================

def remove_inactive_players():
    players = _load_players()
    now = datetime.utcnow()
    removed = []

    for uid, player in list(players.items()):
        last_active = player.get("last_active")

        if not last_active:
            continue

        try:
            last_time = datetime.fromisoformat(last_active)
        except:
            continue

        if now - last_time >= timedelta(days=INACTIVE_DAYS):
            removed.append(uid)
            del players[uid]

    if removed:
        _save_players(players)
        logger.info(f"Удалено {len(removed)} неактивных пользователей")


# ======================
# ИГРОК
# ======================

def get_player(user_id, username=None, tg_username=None):
    remove_inactive_players()

    players = _load_players()
    uid = str(user_id)
    now_iso = datetime.utcnow().isoformat()

    created = False

    if uid not in players:
        created = True
        players[uid] = {
            "user_id": user_id,
            "nickname": None,
            "last_nick_change": None,
            "username": username or f"Игрок {user_id}",
            "tg_username": tg_username or "",
            "money": 0,
            "bank": 0,
            "deposit": 0,
            "last_deposit_put": None,
            "last_deposit_take": None,
            "biz_account": 0,
            "btc": 0.0,
            "energy": ENERGY_MAX,
            "last_energy_tick": time.time(),
            "rating": 0,
            "exp": 0,
            "games_played": 0,
            "status": "Обычный",
            "clan_id": None,
            "property": [],
            "business": [],
            "last_bonus_time": None,
            "last_heist": None,
            "inventory": {},
            "registration_date": now_iso,
            "last_active": now_iso
        }

    player = players[uid]

    if username is not None:
        player["username"] = username

    if tg_username is not None:
        player["tg_username"] = tg_username

    player["last_active"] = now_iso

    _update_energy(player)

    players[uid] = player
    _save_players(players)

    if created:
        logger.info(f"Новый игрок зарегистрирован: {user_id}")
    else:
        logger.info(f"Активность пользователя: {user_id}")

    return player


def save_player(user_id, player):
    players = _load_players()
    players[str(user_id)] = player
    _save_players(players)


# ======================
# ЭНЕРГИЯ
# ======================

def _update_energy(player):
    now = time.time()
    last_tick = player.get("last_energy_tick") or now
    elapsed = now - last_tick
    ticks = int(elapsed // ENERGY_INTERVAL)

    if ticks > 0:
        player["energy"] = min(
            ENERGY_MAX,
            player.get("energy", 0) + ticks * ENERGY_TICK
        )
        player["last_energy_tick"] = last_tick + ticks * ENERGY_INTERVAL


# ======================
# НИК
# ======================

def change_nick(user_id: int, new_nick: str):
    player = get_player(user_id)

    last = player.get("last_nick_change")
    if last:
        last_time = datetime.fromisoformat(last)
        if datetime.utcnow() - last_time < timedelta(days=1):
            return False, "⏳ Ник можно менять раз в сутки"

    player["nickname"] = new_nick
    player["last_nick_change"] = datetime.utcnow().isoformat()

    save_player(user_id, player)
    logger.info(f"Смена ника: {user_id} -> {new_nick}")

    return True, None


def get_mention(user_id: int, username: str = None):
    player = get_player(user_id, username)
    name = player.get("nickname") or player.get("username") or "Игрок"
    return f'<a href="tg://user?id={user_id}">{name}</a>'


# ======================
# BTC
# ======================

def get_btc_balance(user_id):
    return get_player(user_id).get("btc", 0.0)


def change_btc_balance(user_id, amount):
    player = get_player(user_id)
    player["btc"] = round(player.get("btc", 0.0) + amount, 8)
    save_player(user_id, player)
    logger.info(f"BTC изменение: {user_id} | {amount}")


def get_btc_price():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin", "vs_currencies": "usd"},
            timeout=10
        )
        return r.json()["bitcoin"]["usd"]
    except Exception as e:
        logger.error(f"Ошибка получения BTC: {e}")
        return None


# ======================
# ОГРАБЛЕНИЕ
# ======================

def try_heist(user_id: int):
    player = get_player(user_id)
    now = datetime.utcnow()

    last = player.get("last_heist")
    if last:
        last_time = datetime.fromisoformat(last)
        if now - last_time < timedelta(days=1):
            return "cooldown", 0

    success = random.randint(1, 100) <= 45
    reward = 0

    if success:
        reward = random.randint(5_000_000, 15_000_000)
        player["money"] += reward

    player["last_heist"] = now.isoformat()
    save_player(user_id, player)

    logger.info(f"Ограбление: {user_id} | success={success} | reward={reward}")

    return "success" if success else "fail", reward


# ======================
# ВСПОМОГАТЕЛЬНО
# ======================

def can_do_once_per_day(last_time):
    if not last_time:
        return True
    return datetime.utcnow() - datetime.fromisoformat(last_time) >= timedelta(days=1)


def update_usernames(user_id, username=None, tg_username=None):
    player = get_player(user_id)
    if username is not None:
        player["username"] = username
    if tg_username is not None:
        player["tg_username"] = tg_username
    save_player(user_id, player)


def register_or_update_player_interaction(user_id, username=None, tg_username=None):
    return get_player(user_id, username=username, tg_username=tg_username)
