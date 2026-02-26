from aiogram import Router, types
from utils.helpers import get_player, _load_players

router = Router()

# ===== РП действия =====
RP_ACTIONS = {
    "дать пять": "дал(-а) пять",
    "испугать": "испугал(-а)",
    "извиниться": "извинился(-ась) перед",
    "кусь": "сделал(-а) кусь",
    "обнять": "обнял(-а)",
    "поздравить": "поздравил(-а)",
    "поцеловать": "поцеловал(-а)",
    "прижать": "прижал(-а)",
    "пожать руку": "пожал(-а) руку",
    "похвалить": "похвалил(-а)",
    "погладить": "погладил(-а)",
    "дать по лбу": "дал(-а) по лбу",
    "пнуть": "пнул(-а)",
    "покормить": "покормил(-а)",
    "ущипнуть": "ущипнул(-а)",
    "ударить": "ударил(-а)",
    "укусить": "укусил(-а)",
    "шлепнуть": "шлепнул(-а)",
    "убить": "убил(-а)",
    "казнить": "казнил(-а)",
    "воскресить": "воскресил(-а)",
    "изыди": "изгнал(-а)",
    "фейерверк": "запустил(-а) фейерверк с",
    "санки": "катался(-ась) на санках с",
    "сугроб": "нырнул(-а) в сугроб вместе с",
}

# ===== Список команд =====
@router.message(lambda m: m.text and m.text.lower() in ["рп", "рп команды"])
async def rp_list(message: types.Message):
    text = "🎭 <b>РП команды</b>\n\n"
    text += "Использование:\n"
    text += "• ответом на сообщение\n"
    text += "• или: <code>действие @username</code>\n\n"
    text += "🗂 <b>Доступные действия:</b>\n"

    for i, cmd in enumerate(RP_ACTIONS.keys(), 1):
        text += f"{i}) {cmd}\n"

    await message.answer(text, parse_mode="HTML")


# ===== Поиск игрока в базе =====
def find_player(name: str):
    players = _load_players()
    name = name.lower().lstrip("@").strip()

    for pid, p in players.items():
        if not p:
            continue

        nickname = str(p.get("nickname") or "").lower()
        username = str(p.get("username") or "").lower()
        tg_username = str(p.get("tg_username") or "").lower().lstrip("@")

        if name == nickname:
            return int(pid), p
        if name == username:
            return int(pid), p
        if name == tg_username:
            return int(pid), p

    return None, None


# ===== Обработчик РП =====
@router.message(lambda m: m.text and m.text.lower().split()[0] in RP_ACTIONS)
async def rp_action(message: types.Message):
    action_key = message.text.lower().split()[0]
    action_text = RP_ACTIONS[action_key]

    from_user = message.from_user
    from_player = get_player(from_user.id, from_user.first_name, f"@{from_user.username}" if from_user.username else None)
    from_name = from_player.get("nickname") or from_player.get("username") or from_user.first_name
    from_mention = f'<a href="tg://user?id={from_user.id}">{from_name}</a>'

    target_user_id = None
    target_player = None

    # ===== ответом =====
    if message.reply_to_message:
        reply_user = message.reply_to_message.from_user
        target_user_id = reply_user.id
        target_player = get_player(
            target_user_id,
            reply_user.first_name,
            f"@{reply_user.username}" if reply_user.username else None
        )

    # ===== через @ или ник =====
    else:
        parts = message.text.split(maxsplit=1)
        if len(parts) >= 2:
            target_user_id, target_player = find_player(parts[1])

    if not target_player:
        await message.answer("❌ Укажите цель: ответом или @username/ник из базы")
        return

    target_name = target_player.get("nickname") or target_player.get("username") or "Игрок"
    target_mention = f'<a href="tg://user?id={target_user_id}">{target_name}</a>'

    text = f"{from_mention} {action_text} {target_mention}"
    await message.answer(text, parse_mode="HTML")
