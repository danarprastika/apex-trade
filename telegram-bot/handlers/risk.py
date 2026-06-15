from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from clients.backend import BackendClient
from services.formatters import format_percent
from services.token_store import token_store

router = Router()
backend = BackendClient()


@router.callback_query(lambda query: query.data == "risk")
async def risk_callback(query):
    await risk_message(query.message)
    await query.answer()


@router.message(Command("risk"))
async def risk_message(message: Message):
    token = token_store.get(message.chat.id)
    if not token:
        await message.answer("Run /auth <access_token> first.")
        return
    try:
        profile = await backend.get("/risk/profile", token=token)
        events = await backend.get("/risk/events", token=token)
        await message.answer(
            "Risk profile\n"
            f"Max risk/trade: {format_percent(float(profile.get('max_risk_per_trade') or 0))}\n"
            f"Max daily loss: {format_percent(float(profile.get('max_daily_loss') or 0))}\n"
            f"Max drawdown: {format_percent(float(profile.get('max_drawdown') or 0))}\n"
            f"Max open positions: {profile.get('max_open_positions')}\n"
            f"Recent risk events: {len(events)}"
        )
    except Exception as exc:
        await message.answer(f"Failed to load risk profile: {exc}")
