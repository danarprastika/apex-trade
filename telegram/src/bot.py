"""Telegram bot entry point."""

import asyncio
import logging
from aiogram import Bot, Dispatcher

from src.handlers import router as handlers_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Start bot."""
    bot = Bot(token="")
    dp = Dispatcher()
    dp.include_router(handlers_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
