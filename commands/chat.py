from aiogram import Router, types

router = Router()

@router.message(lambda message: message.text and message.text.lower() in ["беседа", "/chat"])
async def chat_cmd(message: types.Message):
    text = (
        "💭 Официальная первая беседа бота:\n"
        "@RafiChatfirst\n\n"
        "💭 Официальный Support беседа бота:\n"
        "@RafiSupportHelp\n\n"
        "💭 Официальный канал разработки:\n"
        "@RafiNews"
    )
    await message.answer(text)
