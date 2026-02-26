# commands/klans/klans_commands.py

from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import logging
from datetime import datetime
from utils.helpers import get_player, save_player, get_mention
from commands.klans.klans_manage import ensure_settings

DATA_FILE = "commands/klans/klans.json"
LOG_DIR = "logs"
LOG_FILE = f"{LOG_DIR}/klans.log"
CLAN_PRICE = 50_000_000  # цена покупки клана

os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("clan_logger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)
if logger.hasHandlers():
    logger.handlers.clear()
logger.addHandler(file_handler)

klans_router = Router()

# ======================
# Работа с базой
# ======================

def _load_clans():
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка чтения базы кланов: {e}")
        return {}

def _save_clans(clans):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(clans, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Ошибка сохранения базы кланов: {e}")

def _next_clan_id(clans):
    if clans:
        return max(int(cid) for cid in clans.keys()) + 1
    return 1

def _sync_player_clan(player, clans):
    clan_id = player.get("clan_id")
    if clan_id is not None and str(clan_id) not in clans:
        player["clan_id"] = None
        save_player(player["id"], player)
    return player

# ======================
# Кнопки
# ======================

def clan_main_kb(clan_id, owner_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔧 Настройки", callback_data=f"clan_settings_{owner_id}_{clan_id}"),
            InlineKeyboardButton(text="👥 Участники", callback_data=f"clan_members_{clan_id}")
        ],
        [
            InlineKeyboardButton(text="👑 Рейтинг Кланов", callback_data="clan_rating")
        ]
    ])

def clan_back_kb(clan_id, owner_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад", callback_data=f"clan_back_{owner_id}_{clan_id}")]
    ])

async def protect_member(call: types.CallbackQuery, clans) -> bool:
    user_id = call.from_user.id
    player = get_player(user_id)

    clan_id = player.get("clan_id")

    if not clan_id or str(clan_id) not in clans:
        await call.answer("⛓ Вы не состоите в клане", show_alert=True)
        return False

    data = call.data

    if data == "clan_rating":
        return True

    parts = data.split("_")

    target_clan_id = None
    for part in reversed(parts):
        if part.isdigit():
            target_clan_id = part
            break

    if target_clan_id and str(clan_id) != str(target_clan_id):
        await call.answer("⛓ Это не ваш клан", show_alert=True)
        return False

    return True

# ======================
# Команды
# ======================

@klans_router.message(F.text.casefold().startswith("создать клан"))
async def create_clan_cmd(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("⚠️ Использование: создать клан НазваниеКлана")
        return

    clan_name = args[2].strip()
    player = get_player(user_id)
    player["id"] = user_id
    clans = _load_clans()
    player = _sync_player_clan(player, clans)

    if player.get("clan_id") is not None:
        await message.answer("⚠️ Вы уже состоите в клане")
        return

    if any(c['name'].lower() == clan_name.lower() for c in clans.values()):
        await message.answer("⚠️ Клан с таким названием уже существует!")
        return

    if player.get("money", 0) < CLAN_PRICE:
        await message.answer(f"⚠️ Недостаточно денег для создания клана ({CLAN_PRICE})")
        return

    cid = _next_clan_id(clans)
    now_iso = datetime.utcnow().isoformat()

    clans[str(cid)] = {
        "id": cid,
        "name": clan_name,
        "owner": user_id,
        "members": [user_id],

        # 🔥 ДОБАВЛЯЕМ БОЕВОЙ СОСТАВ
        "battle_members": [user_id],

        "type": "открытый",
        "rating": 0,
        "exp": 0,
        "money": 0,
        "wins": 0,
        "losses": 0,
        "attacked_by": 0,
        "created_at": now_iso
    }

    player["money"] -= CLAN_PRICE
    player["clan_id"] = cid
    save_player(user_id, player)
    _save_clans(clans)

    await message.answer(f"✅ Клан '{clan_name}' успешно создан")

@klans_router.message(F.text.casefold() == "мой клан")
async def my_clan_cmd(message: types.Message):
    user_id = message.from_user.id
    clans = _load_clans()
    player = get_player(user_id)
    player["id"] = user_id
    player = _sync_player_clan(player, clans)

    clan_id = player.get("clan_id")
    if not clan_id or str(clan_id) not in clans:
        await message.answer("⚠️ Вы не состоите в клане")
        return

    clan = clans[str(clan_id)]

    clan_id_safe = clan.get("id", str(clan_id))
    clan_name = clan.get("name", "Неизвестно")
    clan_type = clan.get("type", "открытый")
    clan_owner = clan.get("owner", user_id)
    members = clan.get("members", [])
    total_exp = sum(get_player(mid).get("exp", 0) for mid in members)
    clan["exp"] = total_exp

    text = (
        f"🏰 Информация о Вашем клане:\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"✏️ Название: {clan_name}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🏰 ID клана: <code>{clan_id}</code>\n"
        f"🔓 Тип клана: {clan_type}\n"
        f"👤 Глава: {get_mention(clan_owner)}\n"
        f"👥 Участников: {len(members)}\n"
        f"👑 Рейтинг Клана: {clan.get('rating',0)}\n"
        f"💪 Сила Клана: {clan.get('exp',0)}\n"
        f"💰 В казне клана: {clan.get('money',0)}\n"
        f"🔥 Побед: {clan.get('wins',0)}, поражений: {clan.get('losses',0)}\n"
        f"🗡 На вас нападало: {clan.get('attacked_by',0)} кланов"
    )

    await message.answer(text, reply_markup=clan_main_kb(clan_id_safe, clan_owner))

# ======================
# CALLBACKS
# ======================

@klans_router.callback_query(
    F.data.startswith("clan_") |
    F.data.startswith("delete_clan_") |
    F.data.startswith("confirm_delete_") |
    F.data.startswith("clan_members_") |
    (F.data == "clan_rating")
)
async def clan_cb(call: types.CallbackQuery):

    clans = _load_clans()

    if not await protect_member(call, clans):
        return

    player = get_player(call.from_user.id)
    player_clan_id = player.get("clan_id")

    data = call.data
    parts = data.split("_")
    clan_id = parts[-1] if parts[-1].isdigit() else parts[-1]
    clan_id_str = str(clan_id)

    if data.startswith("clan_settings_"):

        if clan_id_str not in clans:
            await call.answer("⚠️ Клан не найден", show_alert=True)
            return

        clan = clans[clan_id_str]

        if str(player_clan_id) != clan_id_str:
            await call.answer("⛓ Это не ваш клан", show_alert=True)
            return

        if "settings" not in clan:
            clan["settings"] = {
                "invite": 1,
                "kick": 1,
                "ranks": 1,
                "withdraw": 1,
                "rob": 1,
                "war": 1,
                "rename": 1
            }
            _save_clans(clans)

        s = clan["settings"]

        text = (
            f"{clan['name']}, текущие настройки клана:\n"
            f"[📥] Приглашение: [👑] {s['invite']}\n"
            f"[💢] Кик: [👑] {s['kick']}\n"
            f"[🔰] Управления: [👑] {s['ranks']}\n"
            f"[💵] Снимать с казны: [👑] {s['withdraw']}\n"
            f"[💰] Ограбление: [👑] {s['rob']}\n"
            f"[⚔] Война: [👑] {s['war']}\n"
            f"[✏️] Изменять название: [👑] {s['rename']}\n"
            f"Тип клана: {clan['type']}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="⬅ Назад",
                callback_data=f"clan_back_{clan['owner']}_{clan_id}"
            )]
        ])

        await call.message.edit_text(text, reply_markup=keyboard)
        await call.answer()
        return

    if data.startswith("delete_clan_"):

        if clan_id_str not in clans:
            await call.answer("⚠️ Клан не найден", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Подтвердить удаление",
                callback_data=f"confirm_delete_{parts[-2]}_{clan_id}"
            )],
            [InlineKeyboardButton(
                text="⬅ Назад",
                callback_data=f"clan_back_{parts[-2]}_{clan_id}"
            )]
        ])

        await call.message.edit_text(
            "⚠ Вы уверены, что хотите удалить клан?",
            reply_markup=keyboard
        )

        await call.answer()
        return

    if data.startswith("confirm_delete_"):

        if clan_id_str not in clans:
            await call.answer("⚠️ Клан не найден", show_alert=True)
            return

        clan = clans[clan_id_str]

        for mid in clan.get("members", []):
            p = get_player(mid)
            if p:
                p["clan_id"] = None
                save_player(mid, p)

        del clans[clan_id_str]
        _save_clans(clans)

        await call.message.edit_text("✅ Клан успешно удалён")
        await call.answer()
        return

    if data.startswith("clan_members_"):

        if clan_id_str not in clans:
            await call.answer("⚠️ Клан не найден", show_alert=True)
            return

        clan = ensure_settings(clans[clan_id_str])
        members = clan.get("members", [])

        rank_map = {
            1: "Малый",
            2: "Младший",
            3: "Старший",
            4: "Заместитель",
            5: "Глава"
        }

        players = []

        for mid in members:
            p = get_player(mid)
            if not p:
                continue

            rank = clan.get("members_rank", {}).get(str(mid), 1)

            players.append({
                "id": mid,
                "mention": get_mention(mid),
                "rank": rank,
                "rank_name": rank_map.get(rank, "Неизвестно")
            })

        players.sort(key=lambda x: x["rank"], reverse=True)

        text = (
            f"👥 Участники клана '{clan['name']}'\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Всего участников: {len(members)}\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
        )

        for i, p in enumerate(players, 1):
            text += (
                f"{i}. {p['mention']}\n"
                f"🎖 Ранг: {p['rank_name']}\n"
                f"🆔 ID: <code>{p['id']}</code>\n"
                f"───────────────────\n"
            )

        await call.message.edit_text(
            text,
            reply_markup=clan_back_kb(clan_id_str, clan['owner'])
        )

        await call.answer()
        return

    if data == "clan_rating":

        sorted_clans = sorted(
            clans.values(),
            key=lambda x: x.get("rating", 0),
            reverse=True
        )[:10]

        lines = ["🏆 ТОП 10 КЛАНОВ", "━━━━━━━━━━━━━━━━━━━"]

        if not sorted_clans:
            lines.append("⚠️ Кланов пока нет")
        else:
            medals = ["🥇", "🥈", "🥉"]
            for i, c in enumerate(sorted_clans, 1):
                medal = medals[i - 1] if i <= 3 else "⭐"
                lines.append(
                    f"{medal} {i}. {c.get('name','Неизвестно')}\n"
                    f"📊 Рейтинг: {c.get('rating',0)}\n"
                    f"👥 Участников: {len(c.get('members',[]))}\n"
                    f"───────────────────"
                )

        text = "\n".join(lines)

        player = get_player(call.from_user.id)
        cid = player.get("clan_id", 0)
        owner_id = clans.get(str(cid), {}).get("owner", 0)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="⬅ Назад",
                callback_data=f"clan_back_{owner_id}_{cid}"
            )]
        ])

        await call.message.edit_text(text, reply_markup=keyboard)
        await call.answer()
        return

    if data.startswith("clan_back_"):

        player = get_player(call.from_user.id)
        cid = player.get("clan_id")

        if cid and str(cid) in clans:

            clan = clans[str(cid)]

            total_exp = sum(
                get_player(mid).get("exp", 0)
                for mid in clan.get("members", [])
            )

            clan["exp"] = total_exp

            text = (
                f"🏰 Информация о Вашем клане:\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"✏️ Название: {clan['name']}\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"🏰 ID клана: <code>{cid}</code>\n"
                f"🔓 Тип клана: {clan.get('type','открытый')}\n"
                f"👤 Глава: {get_mention(clan['owner'])}\n"
                f"👥 Участников: {len(clan.get('members',[]))}\n"
                f"👑 Рейтинг: {clan.get('rating',0)}\n"
                f"💪 Сила: {clan.get('exp',0)}\n"
                f"💰 В казне клана: {clan.get('money',0)}\n"
                f"🔥 Побед: {clan.get('wins',0)}, поражений: {clan.get('losses',0)}\n"
                f"🗡 На вас нападало: {clan.get('attacked_by',0)} кланов"
            )

            await call.message.edit_text(
                text,
                reply_markup=clan_main_kb(cid, clan['owner'])
            )

        else:
            await call.message.edit_text("⚠️ Вы не состоите в клане")

        await call.answer()