from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import get_player, save_player, get_mention
from utils.ores import ORE_PRICES

router = Router()
COMMISSION = 0.05  # 5% комиссия

# -------------------
# Инвентарь
# -------------------
@router.message(lambda m: m.text and m.text.strip().lower() == "инвентарь")
async def cmd_inventory(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)
    mention = get_mention(user_id, message.from_user.first_name)

    # Инициализация inventory
    player.setdefault("inventory", {})
    player["inventory"].setdefault("ores", {})
    player["inventory"].setdefault("items", [])

    inventory = player["inventory"]
    items = inventory["items"]
    ores = inventory["ores"]

    if not items and not ores:
        await message.answer(f"🎒 {mention}, твой инвентарь пуст.", parse_mode="HTML")
        return

    text = f"🎒 {mention}, твой инвентарь:\n\n"

    if items:
        text += "📦 Предметы:\n"
        for item in items:
            text += f"• {item}\n"
        text += "\n"

    if ores:
        text += "⛏ Руда:\n"
        for ore, count in ores.items():
            text += f"• {ore.capitalize()} x{count}\n"

    # Кнопка для продажи всей руды
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 Продать руду всё", callback_data="sell_ore_all")]
        ]
    )

    await message.answer(text, parse_mode="HTML", reply_markup=kb)


# -------------------
# Обработчик кнопки "Продать всю руду"
# -------------------
@router.callback_query(lambda c: c.data == "sell_ore_all")
async def sell_ore_all_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    player = get_player(user_id, callback.from_user.first_name)
    mention = get_mention(user_id, callback.from_user.first_name)

    player.setdefault("inventory", {})
    player["inventory"].setdefault("ores", {})
    ores = player["inventory"]["ores"]

    if not ores:
        await callback.answer("❌ У тебя нет руды для продажи.", show_alert=True)
        return

    total_reward = 0
    sold_text = ""
    for ore, count in list(ores.items()):
        reward = round(ORE_PRICES.get(ore, 0) * count * (1 - COMMISSION))
        total_reward += reward
        sold_text += f"• {ore.capitalize()} x{count} → {reward:,}$\n"
        del ores[ore]  # удаляем проданную руду

    player["money"] = player.get("money", 0) + total_reward
    save_player(user_id, player)

    await callback.message.edit_text(
        f"💰 {mention}, ты продал всю руду:\n\n{sold_text}\n📈 Всего получено: {total_reward:,}$",
        parse_mode="HTML"
    )
    await callback.answer()  # закрываем всплывающее уведомление
