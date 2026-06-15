import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from handlers import admin, exchanges, market, portfolio, risk, settings, start, trading

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.include_routers(
    start.router,
    market.router,
    portfolio.router,
    trading.router,
    risk.router,
    exchanges.router,
    settings.router,
    admin.router,
)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
