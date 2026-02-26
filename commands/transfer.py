from aiogram import Router, types
from decimal import Decimal, InvalidOperation
from datetime import datetime
from utils.helpers import get_player, save_player, get_mention, update_usernames, _load_players

router = Router()

DAILY_LIMIT = Decimal("15000000")  # 15 млн в день

# ===== Проверка и сброс лимита =====
def check_reset(player: dict):
    now = datetime.utcnow()
    last_reset = player.get("limit_reset", "")
    today_str = now.strftime("%Y-%m-%d")
    if last_reset != today_str:
        player["limit_sent"] = 0
        player["limit_reset"] = today_str
    return player

# ===== Поиск пользователя СТРОГО из базы =====
def find_user_by_name(name: str):
    players_db = _load_players()
    name = name.lstrip("@").strip().lower()

    for pid, p in players_db.items():
        if not p:
            continue

        nickname = str(p.get("nickname") or "").lower()
        username = str(p.get("username") or "").lower()
        tg_username = str(p.get("tg_username") or "").lower()

        if name == nickname:
            return int(pid), p

        if name == username:
            return int(pid), p

        if tg_username and name == tg_username.lstrip("@"):
            return int(pid), p

    return None, None

# ===== Команда "Дать" =====
@router.message(lambda m: m.text and m.text.lower().startswith("дать"))
async def cmd_give(message: types.Message):
    sender_user = message.from_user
    sender = get_player(sender_user.id, sender_user.first_name, f"@{sender_user.username}" if sender_user.username else None)
    sender = check_reset(sender)
    mention_from = get_mention(sender_user.id, sender_user.first_name or "Игрок")

    parts = message.text.strip().split(maxsplit=2)
    if len(parts) < 2:
        await message.answer(
            f"❌ {mention_from}, используйте: <b>Дать [@user / ответ] [сумма / всё]</b>",
            parse_mode="HTML"
        )
        return

    target_user = None
    target_id = None

    # ===== через ответ =====
    if message.reply_to_message:
        target_user_obj = message.reply_to_message.from_user
        target_id = target_user_obj.id
        target_user = get_player(
            target_id,
            target_user_obj.first_name,
            f"@{target_user_obj.username}" if target_user_obj.username else None
        )

    # ===== через @ или ник из базы =====
    else:
        target_id, target_user = find_user_by_name(parts[1])

    if not target_user:
        await message.answer(
            f"❌ {mention_from}, пользователь не найден в базе.",
            parse_mode="HTML"
        )
        return

    if target_id == sender_user.id:
        await message.answer(f"❌ {mention_from}, вы не можете передавать себе.", parse_mode="HTML")
        return

    mention_to = get_mention(target_id)

    # ===== сумма =====
    if message.reply_to_message:
        amount_text = parts[1] if len(parts) > 1 else ""
    else:
        amount_text = parts[2] if len(parts) > 2 else ""

    if amount_text.lower() in ["всё", "все"]:
        amount = Decimal(sender.get("money", 0))
    else:
        try:
            amount = Decimal(amount_text)
            if amount <= 0:
                raise ValueError
        except:
            await message.answer(
                f"❌ {mention_from}, введите корректную сумму.",
                parse_mode="HTML"
            )
            return

    if amount == 0:
        await message.answer(f"❌ {mention_from}, у вас нет денег.", parse_mode="HTML")
        return

    # ===== лимит =====
    sent_today = Decimal(sender.get("limit_sent", 0))
    remaining = DAILY_LIMIT - sent_today

    if amount > remaining:
        await message.answer(
            f"⚠️ {mention_from}, превышен лимит.\n"
            f"💫 Уже передано: {sent_today:,.2f}$\n"
            f"🚀 Остаток: {remaining:,.2f}$",
            parse_mode="HTML"
        )
        return

    # ===== проверка денег =====
    sender_money = Decimal(sender.get("money", 0))
    if sender_money < amount:
        await message.answer(
            f"❌ {mention_from}, недостаточно средств.",
            parse_mode="HTML"
        )
        return

    # ===== передача =====
    sender["money"] = float(sender_money - amount)
    target_user["money"] = float(Decimal(target_user.get("money", 0)) + amount)
    sender["limit_sent"] = float(sent_today + amount)

    update_usernames(target_id, target_user.get("username"), target_user.get("tg_username"))

    save_player(sender_user.id, sender)
    save_player(target_id, target_user)

    await message.answer(
        f"✅ {mention_from} передал {amount:,.2f}$ {mention_to}",
        parse_mode="HTML"
    )

# ===== лимит =====
@router.message(lambda m: m.text and m.text.lower() in ["лимит", "мой лимит"])
async def cmd_my_limit(message: types.Message):
    user = message.from_user
    player = get_player(user.id, user.first_name, f"@{user.username}" if user.username else None)
    player = check_reset(player)

    sent_today = Decimal(player.get("limit_sent", 0))
    remaining = DAILY_LIMIT - sent_today
    mention = get_mention(user.id, user.first_name)

    await message.answer(
        f"💰 {mention}, ваш лимит:\n"
        f"💫 Уже передано: {sent_today:,.2f}$\n"
        f"🚀 Осталось: {remaining:,.2f}$",
        parse_mode="HTML"
    )
