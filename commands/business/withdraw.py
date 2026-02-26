# commands/business/withdraw.py
from aiogram import Router, types
from utils.helpers import get_player, save_player, get_mention

router = Router()

# ===== Команда "Вывести [сумма / всё]" =====
@router.message(lambda m: m.text and m.text.lower().startswith("вывести"))
async def cmd_withdraw(message: types.Message):
    user = message.from_user
    player = get_player(user.id, user.first_name)
    mention = get_mention(user.id, user.first_name or "Игрок")

    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(f"❌ {mention}, используйте: <b>Вывести [сумма / всё]</b>", parse_mode="HTML")
        return

    amount_text = parts[1].lower()

    # Проверка наличия бизнеса и баланса
    biz_total = player.get("biz_account", 0)
    if biz_total <= 0:
        await message.answer(f"❌ {mention}, у вас нет денег на бизнес-счёте.")
        return

    # Определяем сумму
    if amount_text in ["всё", "все"]:
        amount = biz_total
    else:
        try:
            amount = float(amount_text.replace(".", "").replace(",", ""))
            if amount <= 0:
                raise ValueError
        except ValueError:
            await message.answer(f"❌ {mention}, введите корректную сумму для вывода.", parse_mode="HTML")
            return
        if amount > biz_total:
            await message.answer(f"❌ {mention}, у вас нет столько на бизнес-счёте.\n💳 Баланс: {biz_total:,.0f}$", parse_mode="HTML")
            return

    # Выводим деньги
    player["biz_account"] -= amount
    player["money"] = player.get("money", 0) + amount

    save_player(user.id, player)

    await message.answer(
        f"✅ {mention}, вы успешно вывели {amount:,.0f}$ с бизнес-счёта!\n"
        f"💰 Деньги на руках: {player['money']:,.0f}$\n"
        f"💳 Баланс бизнес-счёта: {player['biz_account']:,.0f}$",
        parse_mode="HTML"
    )
