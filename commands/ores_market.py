from aiogram import Router, types
from utils.helpers import get_player, save_player, get_mention
from utils.ores import ORE_PRICES

router = Router()
COMMISSION = 0.05

# -------------------
# Покупка руды
# -------------------
@router.message(lambda m: m.text and m.text.lower().startswith("купить руду "))
async def buy_ore(message: types.Message):
    args = message.text.lower().split()
    if len(args) != 4:
        await message.answer("❌ Используй: купить руду <название> <кол-во>")
        return

    ore = args[2]
    count = args[3]

    if ore not in ORE_PRICES or not count.isdigit():
        await message.answer("❌ Неверная руда или количество.")
        return

    count = int(count)
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    mention = get_mention(user_id, message.from_user.first_name)

    # инициализация inventory
    player.setdefault("inventory", {})
    player["inventory"].setdefault("ores", {})

    price = ORE_PRICES[ore] * count
    total = round(price * (1 + COMMISSION))

    if player.get("money", 0) < total:
        await message.answer(f"❌ {mention}, недостаточно денег.", parse_mode="HTML")
        return

    player["money"] -= total
    player["inventory"]["ores"][ore] = player["inventory"]["ores"].get(ore, 0) + count
    save_player(user_id, player)

    await message.answer(
        f"✅ {mention}, куплено {ore.capitalize()} x{count}.\n💸 Потрачено: {total:,}$",
        parse_mode="HTML"
    )


# -------------------
# Продажа руды
# -------------------
@router.message(lambda m: m.text and m.text.lower().startswith("продать руду "))
async def sell_ore(message: types.Message):
    args = message.text.lower().split()
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    mention = get_mention(user_id, message.from_user.first_name)

    player.setdefault("inventory", {})
    player["inventory"].setdefault("ores", {})
    ores = player["inventory"]["ores"]

    # Команда "продать руду всё"
    if len(args) == 3 and args[2] == "всё":
        if not ores:
            await message.answer(f"❌ {mention}, у тебя нет руды для продажи.", parse_mode="HTML")
            return

        total_reward = 0
        sold_list = []
        for ore_name, count in list(ores.items()):
            reward = round(ORE_PRICES[ore_name] * count * (1 - COMMISSION))
            total_reward += reward
            sold_list.append(f"{ore_name.capitalize()} x{count}")
            del ores[ore_name]

        player["money"] = player.get("money", 0) + total_reward
        save_player(user_id, player)

        await message.answer(
            f"💰 {mention}, продано всё:\n" + "\n".join(sold_list) + f"\n📈 Получено всего: {total_reward:,}$",
            parse_mode="HTML"
        )
        return

    # Стандартная продажа по количеству
    if len(args) != 4:
        await message.answer("❌ Используй: продать руду <название> <кол-во>")
        return

    ore = args[2]
    count = args[3]

    if ore not in ORE_PRICES or not count.isdigit():
        await message.answer("❌ Неверная руда или количество.")
        return

    count = int(count)

    if ores.get(ore, 0) < count:
        await message.answer(f"❌ {mention}, у вас нет столько руды.", parse_mode="HTML")
        return

    ores[ore] -= count
    if ores[ore] <= 0:
        del ores[ore]

    reward = round(ORE_PRICES[ore] * count * (1 - COMMISSION))
    player["money"] = player.get("money", 0) + reward
    save_player(user_id, player)

    await message.answer(
        f"💰 {mention}, продано {ore.capitalize()} x{count}.\n📈 Получено: {reward:,}$",
        parse_mode="HTML"
    )
