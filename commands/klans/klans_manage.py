from aiogram import Router, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import time
from utils.helpers import get_player, save_player, get_mention
import aiogram

klans_manage_router = Router()

DATA_FILE = "commands/klans/klans.json"
INVITES_FILE = "commands/klans/invites.json"

os.makedirs("commands/klans", exist_ok=True)


# =========================
# БАЗА
# =========================

def load_clans():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_clans(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_invites():
    if not os.path.exists(INVITES_FILE):
        with open(INVITES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(INVITES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_invites(data):
    with open(INVITES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# =========================
# ВСПОМОГАТЕЛЬНОЕ
# =========================

def get_clan_by_player(user_id, clans):
    for cid, clan in clans.items():
        if user_id in clan.get("members", []):
            return cid, clan
    return None, None


def is_owner(user_id, clan):
    return clan.get("owner") == user_id


def ensure_settings(clan):
    if "settings" not in clan:
        clan["settings"] = {
            "invite": 5,
            "kick": 4,
            "ranks": 4,
            "withdraw": 5,
            "rob": 5,
            "war": 4,
            "rename": 3
        }
    if "type" not in clan:
        clan["type"] = "открытый"
    if "money" not in clan:
        clan["money"] = 0
    if "members_rank" not in clan:
        clan["members_rank"] = {str(m): 1 for m in clan.get("members", [])}
        if "owner" in clan:
            clan["members_rank"][str(clan["owner"])] = 5
    return clan


def can_do(user_id, clan, action):
    clan = ensure_settings(clan)
    user_rank = clan["members_rank"].get(str(user_id), 1)
    required_rank = clan["settings"].get(action, 5)
    return user_rank >= required_rank


def rank_name(rank):
    names = {1: "Малый", 2: "Младший", 3: "Старший", 4: "Заместитель", 5: "Глава"}
    return names.get(rank, "Неизвестно")


# =========================
# ТОП КЛАНОВ
# =========================

@klans_manage_router.message(F.text.lower().contains("клан топ"))
async def clan_top(message: Message):
    clans = load_clans()

    top = sorted(
        clans.values(),
        key=lambda x: x.get("rating", 0),
        reverse=True
    )[:10]

    if not top:
        return await message.answer("⚠️ Кланов пока нет")

    lines = []
    lines.append("🏆 ТОП 10 КЛАНОВ")
    lines.append("━━━━━━━━━━━━━━━━━━━")

    medals = ["🥇", "🥈", "🥉"]

    for i, c in enumerate(top, 1):
        medal = medals[i-1] if i <= 3 else "⭐"

        name = c.get("name", "Неизвестно")
        rating = c.get("rating", 0)
        members = len(c.get("members", []))

        lines.append(
            f"{medal} {i}. {name}\n"
            f"📊 Рейтинг: {rating}\n"
            f"👥 Участников: {members}\n"
            f"───────────────────"
        )

    await message.answer("\n".join(lines))
# =========================
# СОЗДАТЬ КЛАН
# =========================

@klans_manage_router.message(F.text.lower().startswith("клан создать"))
async def clan_create(message: Message):
    clans = load_clans()
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await message.answer("⚠️ Использование: клан создать [название]")

    name = parts[2].strip()
    player = get_player(message.from_user.id)

    if player.get("clan_id"):
        return await message.answer("⚠️ Вы уже в клане")

    clan_id = str(int(time.time() * 1000))
    clans[clan_id] = {
        "name": name,
        "owner": message.from_user.id,
        "members": [message.from_user.id],
        "members_rank": {str(message.from_user.id): 5},
        "settings": {
            "invite": 5,
            "kick": 5,
            "ranks": 5,
            "withdraw": 5,
            "rob": 5,
            "war": 5,
            "rename": 5
        },
        "type": "открытый",
        "money": 0,
        "rating": 0
    }

    player["clan_id"] = int(clan_id)
    save_player(message.from_user.id, player)
    save_clans(clans)

    await message.answer(f"🏰 Клан '{name}' создан! ID: {clan_id}")


# =========================
# ПРИГЛАСИТЬ В КЛАН
# =========================

@klans_manage_router.message(F.text.lower().startswith("клан пригласить"))
async def clan_invite(message: Message):
    clans = load_clans()
    invites = load_invites()
    parts = message.text.split()
    if len(parts) < 3:
        return await message.answer("⚠️ Использование: клан пригласить [ID игрока]")

    try:
        target_id = int(parts[2])
    except ValueError:
        return await message.answer("⚠️ ID должен быть числом")

    cid, clan = get_clan_by_player(message.from_user.id, clans)
    if not clan:
        return await message.answer("⚠️ Вы не в клане")

    clan = ensure_settings(clan)
    if not can_do(message.from_user.id, clan, "invite"):
        return await message.answer("⚠️ Ваш ранг не позволяет приглашать")

    if target_id in clan.get("members", []):
        return await message.answer("⚠️ Игрок уже в клане")

    invites[str(target_id)] = str(cid)
    save_invites(invites)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"clan_accept:{cid}"),
                InlineKeyboardButton(text="❌ Отказаться", callback_data=f"clan_decline:{cid}")
            ]
        ]
    )

    try:
        await message.bot.send_message(
            target_id,
            f"📩 Вас пригласили в клан 🏰 '{clan.get('name','Неизвестно')}'\nПринять приглашение?",
            reply_markup=keyboard
        )
    except aiogram.exceptions.TelegramForbiddenError:
        return await message.answer("⚠️ Не удалось отправить приглашение (игрок не начал чат с ботом)")

    await message.answer("✅ Приглашение отправлено игроку")


# =========================
# ВСТУПИТЬ В КЛАН
# =========================

@klans_manage_router.message(F.text.lower().startswith("клан вступить"))
async def clan_join(message: Message):
    clans = load_clans()
    invites = load_invites()
    parts = message.text.split()
    if len(parts) < 3:
        return await message.answer("⚠️ Использование: клан вступить [ID клана]")

    clan_id = parts[2]
    if clan_id not in clans:
        return await message.answer("⚠️ Клан не найден")

    player = get_player(message.from_user.id)
    if player.get("clan_id"):
        return await message.answer("⚠️ Вы уже в клане")

    clan = clans[clan_id]
    clan = ensure_settings(clan)
    if clan.get("type","открытый") == "закрытый" and str(message.from_user.id) not in invites:
        return await message.answer("⚠️ Клан закрытый, нужно приглашение")

    clan.setdefault("members", []).append(message.from_user.id)
    clan.setdefault("members_rank", {})[str(message.from_user.id)] = 1
    player["clan_id"] = int(clan_id)

    if str(message.from_user.id) in invites:
        del invites[str(message.from_user.id)]

    save_player(message.from_user.id, player)
    save_invites(invites)
    save_clans(clans)

    await message.answer(f"🏰 Вы вступили в клан '{clan.get('name','Неизвестно')}'")


# =========================
# ОБРАБОТЧИКИ КНОПОК
# =========================

@klans_manage_router.callback_query(F.data.startswith("clan_accept"))
async def clan_accept(query: types.CallbackQuery):
    clans = load_clans()
    invites = load_invites()
    user_id = query.from_user.id
    cid = query.data.split(":")[1]

    if str(user_id) not in invites or invites[str(user_id)] != cid:
        await query.answer("⚠️ У вас нет приглашения в этот клан", show_alert=True)
        return

    clan = clans.get(cid)
    if not clan:
        del invites[str(user_id)]
        save_invites(invites)
        await query.answer("⚠️ Клан больше не существует", show_alert=True)
        return

    player = get_player(user_id)
    if player.get("clan_id"):
        del invites[str(user_id)]
        save_invites(invites)
        await query.answer("⚠️ Вы уже в клане", show_alert=True)
        return

    clan.setdefault("members", []).append(user_id)
    clan.setdefault("members_rank", {})[str(user_id)] = 1
    player["clan_id"] = int(cid)
    del invites[str(user_id)]

    save_player(user_id, player)
    save_invites(invites)
    save_clans(clans)

    await query.message.edit_text(f"✅ Вы вступили в клан '{clan.get('name','Неизвестно')}'")
    await query.answer("Вы успешно вступили в клан")


@klans_manage_router.callback_query(F.data.startswith("clan_decline"))
async def clan_decline(query: types.CallbackQuery):
    invites = load_invites()
    user_id = query.from_user.id
    cid = query.data.split(":")[1]

    if str(user_id) in invites and invites[str(user_id)] == cid:
        del invites[str(user_id)]
        save_invites(invites)

    await query.message.edit_text("⚠️ Вы отклонили приглашение в клан")
    await query.answer()


# =========================
# ВЫЙТИ ИЗ КЛАНА
# =========================

@klans_manage_router.message(F.text.lower().contains("клан выйти"))
async def clan_leave(message: Message):
    clans = load_clans()
    cid, clan = get_clan_by_player(message.from_user.id, clans)
    if not clan:
        return await message.answer("⚠️ Вы не в клане")

    if is_owner(message.from_user.id, clan):
        return await message.answer("⚠️ Глава не может выйти, передайте клан")

    clan["members"].remove(message.from_user.id)
    del clan["members_rank"][str(message.from_user.id)]

    player = get_player(message.from_user.id)
    player["clan_id"] = None
    save_player(message.from_user.id, player)
    save_clans(clans)

    await message.answer("👞 Вы вышли из клана")


# =========================
# ИСКЛЮЧИТЬ ИЗ КЛАНА
# =========================

@klans_manage_router.message(F.text.lower().startswith("клан кик"))
async def clan_kick(message: Message):
    clans = load_clans()
    parts = message.text.split()
    if len(parts) < 3:
        return await message.answer("⚠️ Использование: клан кик [ID игрока]")

    try:
        target_id = int(parts[2])
    except:
        return await message.answer("⚠️ ID должен быть числом")

    cid, clan = get_clan_by_player(message.from_user.id, clans)
    if not clan:
        return await message.answer("⚠️ Вы не в клане")

    clan = ensure_settings(clan)
    if not can_do(message.from_user.id, clan, "kick"):
        return await message.answer("⚠️ Ваш ранг не позволяет исключать")

    if target_id not in clan["members"]:
        return await message.answer("⚠️ Игрок не в клане")

    if target_id == clan["owner"]:
        return await message.answer("⚠️ Нельзя исключить главу")

    clan["members"].remove(target_id)
    del clan["members_rank"][str(target_id)]

    p = get_player(target_id)
    p["clan_id"] = None
    save_player(target_id, p)
    save_clans(clans)

    await message.answer("👞 Игрок исключён")


# =========================
# ПОВЫСИТЬ И ПОНИЗИТЬ
# =========================

@klans_manage_router.message(F.text.lower().startswith("клан повысить"))
async def clan_promote(message: Message):
    clans = load_clans()
    parts = message.text.split()
    if len(parts) < 3:
        return await message.answer("⚠️ Использование: клан повысить [ID]")

    try:
        target_id = int(parts[2])
    except:
        return await message.answer("⚠️ ID должен быть числом")

    cid, clan = get_clan_by_player(message.from_user.id, clans)
    if not clan:
        return await message.answer("⚠️ Вы не в клане")

    clan = ensure_settings(clan)
    my_rank = clan["members_rank"].get(str(message.from_user.id), 1)
    target_rank = clan["members_rank"].get(str(target_id), 1)

    if target_id not in clan["members"]:
        return await message.answer("⚠️ Игрок не в клане")

    if my_rank <= target_rank or my_rank < 4:
        return await message.answer("⚠️ Вы не можете повысить этого игрока")

    if target_rank >= 4:
        return await message.answer("⚠️ Максимальный ранг для повышения — 4 (кроме главы)")

    clan["members_rank"][str(target_id)] += 1
    save_clans(clans)
    await message.answer(f"✅ Игрок повышен до {rank_name(clan['members_rank'][str(target_id)])}")


@klans_manage_router.message(F.text.lower().startswith("клан понизить"))
async def clan_demote(message: Message):
    clans = load_clans()
    parts = message.text.split()
    if len(parts) < 3:
        return await message.answer("⚠️ Использование: клан понизить [ID]")

    try:
        target_id = int(parts[2])
    except:
        return await message.answer("⚠️ ID должен быть числом")

    cid, clan = get_clan_by_player(message.from_user.id, clans)
    if not clan:
        return await message.answer("⚠️ Вы не в клане")

    clan = ensure_settings(clan)
    my_rank = clan["members_rank"].get(str(message.from_user.id), 1)
    target_rank = clan["members_rank"].get(str(target_id), 1)

    if target_id not in clan["members"]:
        return await message.answer("⚠️ Игрок не в клане")

    if my_rank <= target_rank or my_rank < 4:
        return await message.answer("⚠️ Вы не можете понизить этого игрока")

    if target_rank <= 1:
        return await message.answer("⚠️ Минимальный ранг 1")

    clan["members_rank"][str(target_id)] -= 1
    save_clans(clans)
    await message.answer(f"✅ Игрок понижен до {rank_name(clan['members_rank'][str(target_id)])}")


# =========================
# ПЕРЕДАТЬ ГЛАВУ
# =========================

@klans_manage_router.message(F.text.lower().startswith("клан передать"))
async def clan_transfer(message: Message):
    clans = load_clans()
    parts = message.text.split()
    if len(parts) < 3:
        return await message.answer("⚠️ Использование: клан передать [ID]")

    try:
        target_id = int(parts[2])
    except:
        return await message.answer("⚠️ ID должен быть числом")

    cid, clan = get_clan_by_player(message.from_user.id, clans)
    if not clan:
        return await message.answer("⚠️ Вы не в клане")

    if not is_owner(message.from_user.id, clan):
        return await message.answer("⚠️ Только глава может передать клан")

    if target_id not in clan["members"]:
        return await message.answer("⚠️ Игрок не в клане")

    clan["owner"] = target_id
    clan["members_rank"][str(target_id)] = 5
    clan["members_rank"][str(message.from_user.id)] = 4
    save_clans(clans)
    await message.answer("👑 Клан передан новому Владельцу")


# =========================
# КЛАН КАЗНА
# =========================

@klans_manage_router.message(F.text.lower().startswith("клан казна"))
async def clan_treasury(message: Message):
    clans = load_clans()
    parts = message.text.lower().split()
    cid, clan = get_clan_by_player(message.from_user.id, clans)

    if not clan:
        return await message.answer("⚠️ Вы не в клане")

    clan = ensure_settings(clan)
    player = get_player(message.from_user.id)

    # Просто показать баланс
    if len(parts) == 2:
        return await message.answer(f"💰 В казне: {clan.get('money', 0)}$")

    # =========================
    # СНЯТИЕ ИЗ КАЗНЫ
    # =========================
    if parts[2] == "снять":

        if not can_do(message.from_user.id, clan, "withdraw"):
            return await message.answer("⚠️ Ваш ранг не позволяет снимать с казны")

        if len(parts) < 4:
            return await message.answer("⚠️ Использование: клан казна снять [сумма/всё]")

        # снять всё
        if parts[3] in ["всё", "все"]:
            amount = clan.get("money", 0)

            if amount <= 0:
                return await message.answer("⚠️ В казне нет денег")

            clan["money"] = 0
            player["money"] = player.get("money", 0) + amount

            save_player(message.from_user.id, player)
            save_clans(clans)

            return await message.answer(f"💰 Вы сняли {amount}$ из казны")

        # снять конкретную сумму
        try:
            amount = int(parts[3])
        except:
            return await message.answer("⚠️ Сумма должна быть числом")

        if amount <= 0:
            return await message.answer("⚠️ Сумма должна быть больше 0")

        if clan.get("money", 0) < amount:
            return await message.answer("⚠️ В казне недостаточно денег")

        clan["money"] -= amount
        player["money"] = player.get("money", 0) + amount

        save_player(message.from_user.id, player)
        save_clans(clans)

        return await message.answer(f"💰 Вы сняли {amount}$ из казны")

    # =========================
    # ВНЕСТИ В КАЗНУ
    # =========================
    try:
        amount = int(parts[2])
    except:
        return await message.answer("⚠️ Сумма должна быть числом")

    if amount <= 0:
        return await message.answer("⚠️ Сумма должна быть больше 0")

    if player.get("money", 0) < amount:
        return await message.answer("⚠️ Недостаточно денег")

    player["money"] -= amount
    clan["money"] = clan.get("money", 0) + amount

    save_player(message.from_user.id, player)
    save_clans(clans)

    await message.answer(f"💰 Внесено {amount}$ в казну клана")
# =========================
# КЛАН НАСТРОЙКИ
# =========================

@klans_manage_router.message(F.text.lower().startswith("клан настройки"))
async def clan_settings(message: Message):
    clans = load_clans()
    parts = message.text.lower().split()
    cid, clan = get_clan_by_player(message.from_user.id, clans)
    if not clan:
        return await message.answer("⚠️ Вы не в клане")

    clan = ensure_settings(clan)
    if len(parts) == 2:
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
        return await message.answer(text)

    if not is_owner(message.from_user.id, clan):
        return await message.answer("⚠️ Только глава может менять настройки")

    key_map = {
        "приглашение": "invite",
        "кик": "kick",
        "ранги": "ranks",
        "казна": "withdraw",
        "ограбление": "rob",
        "война": "war",
        "название": "rename",
        "тип": "type"
    }

    if parts[2] not in key_map:
        return await message.answer("⚠️ Неверная настройка")

    key = key_map[parts[2]]

    if key == "type":
        if parts[3] not in ["открытый", "закрытый"]:
            return await message.answer("⚠️ Тип: открытый/закрытый")
        clan["type"] = parts[3]
    else:
        try:
            lvl = int(parts[3])
        except:
            return await message.answer("⚠️ Укажите уровень 1-4")
        if lvl < 1 or lvl > 4:
            return await message.answer("⚠️ Уровень должен быть 1-4")
        clan["settings"][key] = lvl

    save_clans(clans)
    await message.answer("✅ Настройки клана обновлены")


# =========================
# ИЗМЕНИТЬ НАЗВАНИЕ КЛАНА
# =========================

@klans_manage_router.message(F.text.lower().startswith("клан название"))
async def clan_rename(message: Message):
    clans = load_clans()
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await message.answer("⚠️ Использование: клан название [новое название]")

    cid, clan = get_clan_by_player(message.from_user.id, clans)
    if not clan:
        return await message.answer("⚠️ Вы не в клане")

    if not can_do(message.from_user.id, clan, "rename"):
        return await message.answer("⚠️ Ваш ранг не позволяет менять название")

    new_name = parts[2].strip()
    clan["name"] = new_name
    save_clans(clans)
    await message.answer(f"✅ Название клана изменено на '{new_name}'")


# =========================
# УДАЛИТЬ КЛАН (ПОДТВЕРЖДЕНИЕ + CALLBACK)
# =========================

@klans_manage_router.message(F.text.lower().startswith("клан удалить"))
async def clan_delete(message: Message):
    clans = load_clans()

    cid, clan = get_clan_by_player(message.from_user.id, clans)

    if not clan:
        return await message.answer("⚠️ Вы не в клане")

    if not is_owner(message.from_user.id, clan):
        return await message.answer("⚠️ Только глава может удалить клан")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Подтвердить удаление",
                callback_data=f"clan_delete_confirm_{cid}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="clan_delete_cancel"
            )
        ]
    ])

    await message.answer(
        "⚠️ Вы уверены, что хотите удалить клан?\n"
        "Это действие необратимо!",
        reply_markup=keyboard
    )


# =========================
# CALLBACK DELETE HANDLER
# =========================

@klans_manage_router.callback_query(F.data.startswith("clan_delete_"))
async def clan_delete_callback(call: CallbackQuery):
    clans = load_clans()

    # Отмена удаления
    if call.data == "clan_delete_cancel":
        await call.message.edit_text("❌ Удаление клана отменено")
        await call.answer()
        return

    parts = call.data.split("_")
    cid = parts[-1]

    clan = clans.get(cid)

    if not clan:
        await call.answer("⚠️ Клан не найден", show_alert=True)
        return

    # Сброс игроков
    for m in clan.get("members", []):
        p = get_player(m)

        if p:
            p["clan_id"] = None
            save_player(m, p)

    # Удаление клана
    del clans[cid]
    save_clans(clans)

    await call.message.edit_text("✅ Клан успешно удалён")
    await call.answer()