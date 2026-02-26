from aiogram import Router, types

router = Router()

TEXT = (
    "⛏ СИСТЕМА ШАХТ\n"
    "Добыча ресурсов и управление шахтой\n"
    "━━━━━━━━━━━━━━\n"
    "🤖 Ручная добыча\n"
    "копать руду — добывать ресурсы вручную\n"
    "⚡ Тратит энергию\n"
    "📦 Руда сразу идёт в инвентарь\n\n"
    "⚡ Энергия\n"
    "энергия — посмотреть запас энергии\n"
    "🔄 Нужна для ручной добычи\n"
    "━━━━━━━━━━━━━━\n"
    "💡 Подсказка: ручная копка = быстрый фарм\n"
)

@router.message(lambda m: m.text and m.text.lower() in ("шахта", "⛏ шахта"))
async def mine_menu(message: types.Message):
    await message.answer(TEXT)
