from aiogram import Router, types
from utils.helpers import get_player, save_player, get_btc_price
import time

router = Router()

# ===========================
# Кэш курса BTC (обновляем раз в 5 часов)
# ===========================
BTC_CACHE = {"price": None, "time": 0}
BTC_CACHE_TTL = 5 * 3600  # 5 часов

def get_btc_price_safe():
    now = time.time()
    # Если курс ещё не был получен или прошло больше 5 часов
    if BTC_CACHE["price"] is None or now - BTC_CACHE["time"] > BTC_CACHE_TTL:
        price = get_btc_price()
        if price is not None:
            BTC_CACHE["price"] = price
            BTC_CACHE["time"] = now
    return BTC_CACHE["price"]

# ----------------------
# Команда: показать баланс биткоина
# ----------------------
@router.message(lambda message: message.text and message.text.lower().strip() == "биткоин")
async def btc_balance(message: types.Message):
    user = message.from_user
    player = get_player(user.id, user.first_name)
    btc = player.get("btc", 0.0)
    money = player.get("money", 0.0)
    price = get_btc_price_safe()
    if price is None:
        await message.answer("⚠️ Не удалось получить курс BTC. Попробуйте позже.")
        return

    await message.answer(
        f"💎 <a href='tg://user?id={user.id}'>{user.first_name}</a>, ваш баланс BTC:\n"
        f"💽 Биткоинов: {btc:.8f} BTC\n"
        f"💰 Денег: {money:,.2f}$\n"
        f"📈 Текущий курс BTC: {price:,.2f}$",
        parse_mode="HTML"
    )

# ----------------------
# Команда: показать курс биткоина
# ----------------------
@router.message(lambda message: message.text and message.text.lower().strip() == "биткоин курс")
async def btc_price(message: types.Message):
    user = message.from_user
    price = get_btc_price_safe()
    if price is None:
        await message.answer("⚠️ Не удалось получить курс BTC. Попробуйте позже.")
        return
    await message.answer(
        f"📈 <a href='tg://user?id={user.id}'>{user.first_name}</a>, текущий курс Bitcoin:\n"
        f"💰 1 BTC = {price:,.2f}$",
        parse_mode="HTML"
    )

# ----------------------
# Команда: купить биткоин
# ----------------------
@router.message(lambda message: message.text and message.text.lower().startswith("купить биткоин"))
async def btc_buy(message: types.Message):
    user = message.from_user
    player = get_player(user.id, user.first_name)
    parts = message.text.strip().split()
    if len(parts) != 3:
        await message.answer("❌ Используйте: купить биткоин <кол-во>")
        return
    try:
        amount = float(parts[2])
        if amount <= 0:
            raise ValueError
    except:
        await message.answer("❌ Введите корректное количество BTC больше 0.")
        return

    price = get_btc_price_safe()
    if price is None:
        await message.answer("⚠️ Не удалось получить курс BTC.")
        return

    total_cost = amount * price
    if player["money"] < total_cost:
        await message.answer(f"❌ У вас недостаточно денег. Нужно {total_cost:,.2f}$")
        return

    player["money"] -= total_cost
    player["btc"] = player.get("btc", 0.0) + amount
    save_player(user.id, player)

    await message.answer(
        f"🎉 <a href='tg://user?id={user.id}'>{user.first_name}</a>, вы купили {amount:.8f} BTC за {total_cost:,.2f}$!\n\n"
        f"💎 Новый баланс:\n"
        f"💰 Денег: {player['money']:,.2f}$\n"
        f"💽 Биткоинов: {player['btc']:.8f} BTC",
        parse_mode="HTML"
    )

# ----------------------
# Команда: продать биткоин
# ----------------------
@router.message(lambda message: message.text and message.text.lower().startswith("продать биткоин"))
async def btc_sell(message: types.Message):
    user = message.from_user
    player = get_player(user.id, user.first_name)
    parts = message.text.strip().split()
    if len(parts) != 3:
        await message.answer("❌ Используйте: продать биткоин <кол-во>")
        return
    try:
        amount = float(parts[2])
        if amount <= 0:
            raise ValueError
    except:
        await message.answer("❌ Введите корректное количество BTC больше 0.")
        return

    btc_balance = player.get("btc", 0.0)
    if btc_balance < amount:
        await message.answer(f"❌ У вас нет столько BTC. Баланс: {btc_balance:.8f} BTC")
        return

    price = get_btc_price_safe()
    if price is None:
        await message.answer("⚠️ Не удалось получить курс BTC.")
        return

    total_gain = amount * price
    player["btc"] -= amount
    player["money"] += total_gain
    save_player(user.id, player)

    await message.answer(
        f"💰 <a href='tg://user?id={user.id}'>{user.first_name}</a>, вы продали {amount:.8f} BTC за {total_gain:,.2f}$!\n\n"
        f"💎 Новый баланс:\n"
        f"💰 Денег: {player['money']:,.2f}$\n"
        f"💽 Биткоинов: {player['btc']:.8f} BTC",
        parse_mode="HTML"
    )
