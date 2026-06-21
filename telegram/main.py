"""Telegram bot entry point."""
import asyncio

from aiogram import Bot, Dispatcher

from app.infrastructure.messaging.telegram.bot import create_dispatcher
from app.infrastructure.messaging.telegram.middlewares import setup_middlewares


async def main() -> None:
    bot = Bot(token="")
    dp = create_dispatcher()
    setup_middlewares(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
