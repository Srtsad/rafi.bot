import json
import os

ORES_FILE = "database/ores.json"

ORE_PRICES = {
    "железо": 120_000,
    "золото": 450_000,
    "алмаз": 2_500_000,
    "аметист": 4_000_000,
    "аквамарин": 6_500_000,
    "изумруд": 9_000_000,
    "кварциум": 15_000_000,
    "материя": 22_000_000,
    "плазма": 35_000_000,
    "нейронит": 50_000_000,
    "никель": 75_000_000,
    "астролит": 120_000_000,
    "титан": 200_000_000,
    "кобальт": 300_000_000,
    "энергон": 450_000_000,
    "эктоплазма": 600_000_000,
    "хрононий": 800_000_000,
    "генезиум": 1_000_000_000,
    "палладий": 1_500_000_000
}


def _load():
    if not os.path.exists(ORES_FILE):
        os.makedirs(os.path.dirname(ORES_FILE), exist_ok=True)
        with open(ORES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(ORES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data):
    with open(ORES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_ores(user_id: int) -> dict:
    data = _load()
    return data.get(str(user_id), {})


def add_ore(user_id: int, ore: str, amount: int):
    data = _load()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {}

    data[uid][ore] = data[uid].get(ore, 0) + amount
    _save(data)


def remove_ore(user_id: int, ore: str, amount: int) -> bool:
    data = _load()
    uid = str(user_id)

    if uid not in data:
        return False

    if data[uid].get(ore, 0) < amount:
        return False

    data[uid][ore] -= amount

    if data[uid][ore] <= 0:
        del data[uid][ore]

    _save(data)
    return True
