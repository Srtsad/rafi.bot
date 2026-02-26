from aiogram import Router, types
from aiogram.types import CallbackQuery
from utils.helpers import (
    get_player,
    save_player,
    ENERGY_MAX,
    ENERGY_INTERVAL,
    ENERGY_TICK
)
from keyboards.profile_kb import profile_buttons, back_to_profile
import time

router = Router()


# ==================================================
# ЗАЩИТА КНОПОК
# ==================================================
async def protect_owner(call: CallbackQuery) -> bool:
    try:
        owner_id = int(call.data.split(":")[1])
    except:
        await call.answer()
        return False

    if call.from_user.id != owner_id:
        await call.answer("⛓ Это не ваша кнопка.")
        return False

    return True


# ==================================================
# ФОРМАТ ЧИСЕЛ
# ==================================================
def fmt(n):
    return f"{int(n):,}".replace(",", ".")


# ==================================================
# ФОРМАТ ИМУЩЕСТВА
# ==================================================
def format_property(player):
    property_list = player.get("property", [])
    if not property_list:
        return "🏡 У вас нет имущества."

    categories = {
        "Самолёты": [],
        "Машины": [],
        "Телефоны": [],
        "Яхты": [],
        "Вертолёты": [],
        "Дома": [],
        "Прочее": []
    }

    for item in property_list:
        if isinstance(item, dict):
            typ = item.get("type", "other")
            emoji = item.get("emoji", "")
            name = item.get("name", "Неизвестно")
            price = fmt(item.get("price", 0))
            line = f"{emoji} {name} — куплено за {price}$"

            if typ == "plane":
                categories["Самолёты"].append(line)
            elif typ == "car":
                categories["Машины"].append(line)
            elif typ == "phone":
                categories["Телефоны"].append(line)
            elif typ == "yacht":
                categories["Яхты"].append(line)
            elif typ == "heli":
                categories["Вертолёты"].append(line)
            elif typ == "house":
                categories["Дома"].append(line)
            else:
                categories["Прочее"].append(line)
        else:
            categories["Прочее"].append(str(item))

    lines = ["🏡 <b>Ваше имущество:</b>\n"]
    for cat, items in categories.items():
        if items:
            lines.append(f"📌 <b>{cat}</b>")
            lines.extend([f"{idx+1}. {line}" for idx, line in enumerate(items)])
            lines.append("")
    return "\n".join(lines)


# ==================================================
# ОБНОВЛЕНИЕ ЭНЕРГИИ
# ==================================================
def update_energy(player, user_id):
    now = time.time()
    last_tick = player.get("last_energy_tick", now)
    elapsed = now - last_tick
    ticks = int(elapsed // ENERGY_INTERVAL)

    if ticks > 0:
        player["energy"] = min(
            ENERGY_MAX,
            player.get("energy", 0) + ticks * ENERGY_TICK
        )
        player["last_energy_tick"] = last_tick + ticks * ENERGY_INTERVAL
        save_player(user_id, player)

    return player.get("energy", 0)


# ==================================================
# КОМАНДА "ПРОФИЛЬ"
# ==================================================
@router.message(lambda m: m.text and m.text.lower() == "профиль")
async def profile_cmd(message: types.Message):
    user_id = message.from_user.id
    player = get_player(user_id, message.from_user.first_name)

    energy = update_energy(player, user_id)

    display_name = player.get("nickname") or player.get("username") or message.from_user.first_name
    mention = f'<a href="tg://user?id={user_id}">{display_name}</a>'

    clan_id = player.get("clan_id") or "Нет"

    text = (
        f"{mention}, ваш профиль:\n"
        f"🪪 ID: <a href='tg://user?id={user_id}'>{user_id}</a>\n"
        f"🏆 Статус: {player.get('status','Новичок')}\n"
        f"💰 Денег: {fmt(player.get('money',0))}$\n"
        f"🏦 В банке: {fmt(player.get('bank',0))}$\n"
        f"💳 Бизнес счёт: {fmt(player.get('biz_account',0))}$\n"
        f"💽 Биткоины: {fmt(player.get('btc',0))}\n"
        f"🏋 Энергия: {energy}\n"
        f"👑 Рейтинг Клана: {player.get('rating',0)}\n"
        f"🏰 ID клана: {clan_id}\n"
        f"💪 Сила: {player.get('exp',0)}\n"
        f"🎲 Всего сыграно игр: {player.get('games_played',0)}\n\n"
        f"<blockquote>"
        f"📅 Дата регистрации: {player.get('registration_date','Сегодня')}"
        f"</blockquote>"
    )

    await message.answer(
        text,
        reply_markup=profile_buttons(user_id),
        parse_mode="HTML"
    )


# ==================================================
# CALLBACK: НАЗАД В ПРОФИЛЬ
# ==================================================
@router.callback_query(lambda c: c.data.startswith("profile_back:"))
async def profile_back(call: CallbackQuery):
    if not await protect_owner(call):
        return

    player = get_player(call.from_user.id)
    energy = update_energy(player, call.from_user.id)

    display_name = player.get("nickname") or player.get("username") or "Игрок"
    mention = f'<a href="tg://user?id={call.from_user.id}">{display_name}</a>'

    clan_id = player.get("clan_id") or "Нет"

    text = (
        f"{mention}, ваш профиль:\n"
        f"🪪 ID: {call.from_user.id}\n"
        f"🏆 Статус: {player.get('status','Новичок')}\n"
        f"💰 Денег: {fmt(player.get('money',0))}$\n"
        f"🏦 В банке: {fmt(player.get('bank',0))}$\n"
        f"💳 Бизнес счёт: {fmt(player.get('biz_account',0))}$\n"
        f"💽 Биткоины: {fmt(player.get('btc',0))}\n"
        f"🏋 Энергия: {energy}\n"
        f"👑 Рейтинг Клана: {player.get('rating',0)}\n"
        f"🏰 ID клана: {clan_id}\n"
        f"💪 Сила: {player.get('exp',0)}\n"
        f"🎲 Всего сыграно игр: {player.get('games_played',0)}\n\n"
        f"<blockquote>"
        f"📅 Дата регистрации: {player.get('registration_date','Сегодня')}"
        f"</blockquote>"
    )

    await call.message.edit_text(
        text,
        reply_markup=profile_buttons(call.from_user.id),
        parse_mode="HTML"
    )
    await call.answer()


# ==================================================
# CALLBACK: ИМУЩЕСТВО
# ==================================================
@router.callback_query(lambda c: c.data.startswith("profile_property:"))
async def profile_property(call: CallbackQuery):
    if not await protect_owner(call):
        return

    player = get_player(call.from_user.id)
    text = format_property(player)

    await call.message.edit_text(
        text,
        reply_markup=back_to_profile(call.from_user.id),
        parse_mode="HTML"
    )
    await call.answer()


# ==================================================
# CALLBACK: БИЗНЕС
# ==================================================
@router.callback_query(lambda c: c.data.startswith("profile_business:"))
async def profile_business(call: CallbackQuery):
    if not await protect_owner(call):
        return

    player = get_player(call.from_user.id)
    biz_list = player.get("business", [])

    if biz_list:
        text = "💼 <b>Ваш бизнес:</b>\n" + "\n".join(biz_list)
    else:
        text = "💼 У вас нет бизнеса."

    await call.message.edit_text(
        text,
        reply_markup=back_to_profile(call.from_user.id),
        parse_mode="HTML"
    )
    await call.answer()


# ==================================================
# КОМАНДА "ИМУЩЕСТВО"
# ==================================================
@router.message(lambda m: m.text and m.text.lower() == "имущество")
async def property_cmd(message: types.Message):
    player = get_player(message.from_user.id)
    text = format_property(player)

    await message.answer(
        text,
        reply_markup=back_to_profile(message.from_user.id),
        parse_mode="HTML"
    )


# ==================================================
# КОМАНДА "МОИ БИЗНЕСЫ"
# ==================================================
@router.message(lambda m: m.text and m.text.lower() in ["мои бизнесы", "бизнесы", "бизы"])
async def cmd_my_businesses(message: types.Message):
    player = get_player(message.from_user.id)
    businesses = player.get("business", [])

    if businesses:
        text = "💼 <b>Твои бизнесы:</b>\n" + "\n".join(businesses)
    else:
        text = "💼 <b>У тебя нет бизнесов.</b>"

    await message.answer(
        text,
        reply_markup=back_to_profile(message.from_user.id),
        parse_mode="HTML"
    )