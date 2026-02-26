# commands/games/marry.py

import asyncio
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from utils.helpers import get_player, save_player

marry_router = Router()


def mention(user_id, name="Игрок"):
    return f'<a href="tg://user?id={user_id}">{name}</a>'


# ===================== 💍 ПРЕДЛОЖЕНИЕ =====================
@marry_router.message(lambda m: m.text and m.text.lower().startswith("свадьба"))
async def marry_cmd(message: types.Message):
    user1 = message.from_user
    player1 = get_player(user1.id)

    if player1.get("married"):
        await message.answer("❌ Ты уже состоишь в браке.")
        return

    if not message.reply_to_message:
        await message.answer("Ответь на сообщение игрока командой: свадьба")
        return

    target = message.reply_to_message.from_user

    if target.id == user1.id:
        await message.answer("🤡 Сам с собой нельзя.")
        return

    player2 = get_player(target.id)

    if player2.get("married"):
        await message.answer("❌ Этот игрок уже в браке.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💍 Согласиться", callback_data=f"marry_yes_{user1.id}_{target.id}"),
            InlineKeyboardButton(text="❌ Отказать", callback_data=f"marry_no_{user1.id}_{target.id}")
        ]
    ])

    text = (
        f"💍 <b>Предложение брака!</b>\n\n"
        f"{mention(user1.id)} предлагает руку и сердце\n"
        f"{mention(target.id)} ❤️\n\n"
        f"Ответь ниже 👇"
    )

    sent_msg = await message.answer(text, reply_markup=kb, parse_mode="HTML")

    async def expire_proposal():
        await asyncio.sleep(30)
        try:
            msg = await message.bot.get_message(chat_id=sent_msg.chat.id, message_id=sent_msg.message_id)
        except Exception:
            return

        if msg.reply_markup:
            await sent_msg.edit_reply_markup(None)
            await message.answer(
                f"⏳ {mention(user1.id)}, ваше предложение брака не было принято 😔",
                parse_mode="HTML"
            )

    asyncio.create_task(expire_proposal())


# ===================== ✔ СОГЛАСИЕ =====================
@marry_router.callback_query(F.data.startswith("marry_yes_"))
async def marry_yes(call: CallbackQuery):
    parts = call.data.split("_")
    proposer_id = int(parts[2])
    target_id = int(parts[3])
    accepter = call.from_user

    if accepter.id != target_id:
        await call.answer("⛓ Это не ваше предложение.", show_alert=False)
        return

    player1 = get_player(proposer_id)
    player2 = get_player(accepter.id)

    if player1.get("married") or player2.get("married"):
        await call.answer("Кто-то уже в браке.", show_alert=True)
        return

    player1["married"] = accepter.id
    player2["married"] = proposer_id

    save_player(proposer_id, player1)
    save_player(accepter.id, player2)

    text = (
        f"💍 <b>НОВАЯ СЕМЬЯ!</b>\n\n"
        f"{mention(proposer_id)} ❤️ {mention(accepter.id)}\n"
        f"Теперь вы официально вместе 🥂"
    )

    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer("Вы поженились 💍")


# ===================== ❌ ОТКАЗ =====================
@marry_router.callback_query(F.data.startswith("marry_no_"))
async def marry_no(call: CallbackQuery):
    parts = call.data.split("_")
    proposer_id = int(parts[2])
    target_id = int(parts[3])
    user = call.from_user

    if user.id != target_id:
        await call.answer("⛓ Это не ваше предложение.", show_alert=False)
        return

    text = (
        f"💔 {mention(user.id)} отклонил(а) предложение\n"
        f"от {mention(proposer_id)}"
    )

    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer("Отказ отправлен")


# ===================== 💔 РАЗВОД (ПОДТВЕРЖДЕНИЕ) =====================
@marry_router.message(lambda m: m.text and m.text.lower() == "развод")
async def divorce_cmd(message: types.Message):
    user = message.from_user
    player = get_player(user.id)

    if not player.get("married"):
        await message.answer("❌ Ты не в браке.")
        return

    partner_id = player["married"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💔 Развестись", callback_data=f"divorce_yes_{user.id}"),
            InlineKeyboardButton(text="🔙 Отменить", callback_data=f"divorce_no_{user.id}")
        ]
    ])

    text = (
        f"⚠️ <b>Подтверждение развода</b>\n\n"
        f"{mention(user.id)}, вы действительно хотите разорвать брак?\n"
        f"Это действие нельзя отменить.\n\n"
        f"Если вы уверены — нажмите кнопку ниже 👇"
    )

    await message.answer(text, reply_markup=kb, parse_mode="HTML")


# ===================== ✔ ПОДТВЕРЖДЕНИЕ РАЗВОДА =====================
@marry_router.callback_query(F.data.startswith("divorce_yes_"))
async def divorce_yes(call: CallbackQuery):
    user_id = int(call.data.split("_")[2])

    if call.from_user.id != user_id:
        await call.answer("⛓ Это не ваше действие.", show_alert=False)
        return

    player = get_player(user_id)

    if not player.get("married"):
        await call.answer("Вы уже не в браке.", show_alert=True)
        return

    partner_id = player["married"]
    partner = get_player(partner_id)

    player["married"] = None
    partner["married"] = None

    save_player(user_id, player)
    save_player(partner_id, partner)

    text = (
        f"💔 <b>Развод оформлен</b>\n\n"
        f"{mention(user_id)} и {mention(partner_id)}\n"
        f"больше не состоят в браке."
    )

    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer("Брак расторгнут 💔")


# ===================== ❌ ОТМЕНА РАЗВОДА =====================
@marry_router.callback_query(F.data.startswith("divorce_no_"))
async def divorce_no(call: CallbackQuery):
    user_id = int(call.data.split("_")[2])

    if call.from_user.id != user_id:
        await call.answer("⛓ Это не ваше действие.", show_alert=False)
        return

    await call.message.edit_text("❤️ Развод отменён. Берегите свою любовь.")
    await call.answer("Отменено")


# ===================== ❤️ МОЙ БРАК =====================
@marry_router.message(lambda m: m.text and m.text.lower() in ["мой брак", "брак"])
async def my_marry(message: types.Message):
    user = message.from_user
    player = get_player(user.id)

    if not player.get("married"):
        await message.answer("💔 Ты не состоишь в браке.")
        return

    partner_id = player["married"]

    text = (
        f"💍 Твой партнёр:\n"
        f"{mention(partner_id)} ❤️"
    )

    await message.answer(text, parse_mode="HTML")