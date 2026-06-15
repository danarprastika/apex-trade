from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from clients.backend import BackendClient
from services.token_store import token_store

router = Router()
backend = BackendClient()


@router.message(Command("market"))
async def market_message(message: Message):
    token = token_store.get(message.chat.id)
    if not token:
        await message.answer("Run /auth <access_token> first.")
        return
    try:
        pairs = await backend.get("/market/pairs", token=token)
        assets = await backend.get("/market/assets", token=token)
        await message.answer(
            f"Market overview\nPairs: {len(pairs)}\nAssets: {len(assets)}\nUse the web dashboard for charts and candles."
        )
    except Exception as exc:
        await message.answer(f"Failed to load market data: {exc}")
