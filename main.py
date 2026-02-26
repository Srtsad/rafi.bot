import asyncio
import logging

from aiogram import Dispatcher
from core.bot import bot
from core.dispatcher import setup_dispatcher

CHAT_ID = -1003392460122  # <-- сюда вставь ID чата для уведомления

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    print("\n🤖 Бот запущен — Rafi")
    print("━━━━━━━━━━━━━━━━━━━━")
    print("🚀 Статус: ONLINE")
    print("💬 Ожидаю сообщения...\n")

    dp = Dispatcher(bot=bot)
    setup_dispatcher(dp)

    try:
        await dp.start_polling(bot)  # запускаем polling
    except KeyboardInterrupt:
        print("\n⚠️ Получен Ctrl+C, уведомляем чат...")
        try:
            await bot.send_message(CHAT_ID, "⚠️ Бот перезапускается…")
        except Exception as e:
            print(f"❌ Не удалось отправить сообщение: {e}")
    finally:
        # безопасно закрываем polling и сессию
        try:
            await dp.stop_polling()
        except Exception:
            pass
        await bot.session.close()
        print("🛑 Бот выключен.")

if __name__ == "__main__":
    asyncio.run(main())
