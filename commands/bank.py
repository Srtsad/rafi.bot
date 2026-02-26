from aiogram import Router, types
from datetime import datetime, timedelta
from utils.helpers import get_player, save_player, get_mention

router = Router()

DEPOSIT_PERCENT = 6  # %
BANK_TAX = 5  # %
DEPOSIT_COOLDOWN = timedelta(days=1)

# =====================
# Проверка и создание полей у игрока
# =====================
def ensure_bank_fields(player):
    if "bank" not in player:
        player["bank"] = 0
    if "deposit" not in player:
        player["deposit"] = 0
    if "last_deposit_time" not in player:
        player["last_deposit_time"] = None
    return player

# =====================
# Стата банка
# =====================
@router.message(lambda m: m.text and m.text.strip().lower() == "банк")
async def cmd_bank(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    player = ensure_bank_fields(player)

    mention = get_mention(user_id, message.from_user.first_name)
    bank_fmt = f"{player['bank']:,}".replace(",", ".")
    deposit_fmt = f"{player['deposit']:,}".replace(",", ".")

    last_time = player.get("last_deposit_time")
    if last_time:
        try:
            next_withdraw = datetime.fromisoformat(last_time) + DEPOSIT_COOLDOWN
            next_withdraw_str = next_withdraw.strftime("%d.%m.%y в %H:%M:%S")
        except:
            next_withdraw_str = "Сейчас"
    else:
        next_withdraw_str = "Сейчас"

    text = (
        f"{mention}, ваш банковский счёт:\n"
        f"👫 Владелец: {mention}\n"
        f"💰 Деньги в банке: {bank_fmt}$\n"
        f"💎 Статус: {player.get('status','Обычный')}\n"
        f"〽 Процент под депозит: {DEPOSIT_PERCENT}%\n"
        f"💱 Налог на снятие: {BANK_TAX}%\n"
        f"💵 Под депозитом: {deposit_fmt}$\n"
        f"⏳ Можно снять: {next_withdraw_str}"
    )
    await message.answer(text, parse_mode="HTML")

# =====================
# Команды Банк [положить/снять] сумма
# =====================
@router.message(lambda m: m.text and m.text.strip().lower().startswith("банк "))
async def cmd_bank_actions(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    player = ensure_bank_fields(player)

    mention = get_mention(user_id)

    parts = message.text.strip().split()
    if len(parts) < 3:
        await message.answer(f"{mention}, используйте: Банк [положить/снять] [сумма/всё]")
        return

    action = parts[1].lower()
    amount_text = parts[2].lower()
    bank_balance = player["bank"]
    money_balance = player["money"]

    if amount_text in ["всё", "все"]:
        amount = money_balance if action == "положить" else bank_balance
    else:
        try:
            amount = int(amount_text)
            if amount <= 0:
                raise ValueError
        except:
            await message.answer(f"{mention}, введите корректную сумму.")
            return

    if action == "положить":
        if money_balance < amount:
            await message.answer(f"{mention}, у вас недостаточно денег для депозита.")
            return
        player["money"] -= amount
        player["bank"] += amount
        save_player(user_id, player)
        await message.answer(f"{mention}, вы положили {amount:,}$ в банк.".replace(",", "."))
    elif action == "снять":
        tax = int(amount * BANK_TAX / 100)
        total = amount + tax
        if bank_balance < total:
            await message.answer(f"{mention}, в банке недостаточно средств для снятия с учётом налога.")
            return
        player["bank"] -= total
        player["money"] += amount
        save_player(user_id, player)
        await message.answer(f"{mention}, вы сняли {amount:,}$ с банка (налог {tax:,}$).".replace(",", "."))
    else:
        await message.answer(f"{mention}, действие должно быть 'положить' или 'снять'.")

# =====================
# Если написали просто "депозит"
# =====================
@router.message(lambda m: m.text and m.text.strip().lower() == "депозит")
async def deposit_help(message: types.Message):
    mention = get_mention(message.from_user.id, message.from_user.first_name)

    await message.answer(
        f"{mention}, напишите правильно:\n"
        f"Депозит положить [сумма]\n"
        f"Депозит снять [сумма]\n\n"
        f"Пример:\n"
        f"депозит положить 1000000\n"
        f"депозит снять всё",
        parse_mode="HTML"
    )

# =====================
# Команды Депозит [положить/снять] сумма
# =====================
@router.message(lambda m: m.text and m.text.strip().lower().startswith("депозит "))
async def cmd_deposit(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    player = ensure_bank_fields(player)

    mention = get_mention(user_id)
    now = datetime.utcnow()

    parts = message.text.strip().split()
    if len(parts) < 3:
        await message.answer(f"{mention}, используйте: Депозит [положить/снять] [сумма/всё]")
        return

    action = parts[1].lower()
    amount_text = parts[2].lower()
    bank_balance = player["bank"]
    deposit_balance = player["deposit"]

    # проверка cooldown
    last_time = player.get("last_deposit_time")
    if last_time:
        last_dt = datetime.fromisoformat(last_time)
        if now - last_dt < DEPOSIT_COOLDOWN:
            await message.answer(f"{mention}, депозит можно менять раз в сутки.")
            return

    if amount_text in ["всё", "все"]:
        amount = bank_balance if action == "положить" else deposit_balance
    else:
        try:
            amount = int(amount_text)
            if amount <= 0:
                raise ValueError
        except:
            await message.answer(f"{mention}, введите корректную сумму.")
            return

    if action == "положить":
        if bank_balance < amount:
            await message.answer(f"{mention}, в банке недостаточно денег для депозита.")
            return
        player["bank"] -= amount
        player["deposit"] += amount
        player["last_deposit_time"] = now.isoformat()
        save_player(user_id, player)
        await message.answer(f"{mention}, вы положили {amount:,}$ на депозит.".replace(",", "."))
    elif action == "снять":
        if deposit_balance < amount:
            await message.answer(f"{mention}, на депозите недостаточно денег.")
            return
        player["deposit"] -= amount
        player["bank"] += amount
        player["last_deposit_time"] = now.isoformat()
        save_player(user_id, player)
        await message.answer(f"{mention}, вы сняли {amount:,}$ с депозита.".replace(",", "."))
    else:
        await message.answer(f"{mention}, действие должно быть 'положить' или 'снять'.")
