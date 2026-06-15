from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from clients.backend import BackendClient
from services.formatters import format_money
from services.token_store import token_store

router = Router()
backend = BackendClient()


@router.callback_query(lambda query: query.data == "signals")
async def signals_callback(query: CallbackQuery):
    await signals_message(query.message)
    await query.answer()


@router.message(Command("signals"))
async def signals_message(message: Message):
    token = token_store.get(message.chat.id)
    if not token:
        await message.answer("Run /auth <access_token> first.")
        return
    try:
        signals = await backend.get("/trading/signals", token=token)
        if not signals:
            await message.answer("No signals found.")
            return
        lines = [
            f"{signal.get('market_pair_id')} {signal.get('signal_type')} confidence {signal.get('confidence')} entry {signal.get('entry_price')}"
            for signal in signals[:5]
        ]
        await message.answer("Latest signals:\n" + "\n".join(lines))
    except Exception as exc:
        await message.answer(f"Failed to load signals: {exc}")


@router.message(Command("orders"))
async def orders_message(message: Message):
    token = token_store.get(message.chat.id)
    if not token:
        await message.answer("Run /auth <access_token> first.")
        return
    try:
        orders = await backend.get("/trading/orders", token=token)
        if not orders:
            await message.answer("No orders found.")
            return
        lines = [
            f"#{order.get('id')} {order.get('side')} {order.get('quantity')} {order.get('status')}"
            for order in orders[:5]
        ]
        await message.answer("Latest orders:\n" + "\n".join(lines))
    except Exception as exc:
        await message.answer(f"Failed to load orders: {exc}")


@router.message(Command("paperbuy"))
async def paper_buy(message: Message):
    await _paper_order(message, "BUY")


@router.message(Command("papersell"))
async def paper_sell(message: Message):
    await _paper_order(message, "SELL")


async def _paper_order(message: Message, side: str):
    token = token_store.get(message.chat.id)
    if not token:
        await message.answer("Run /auth <access_token> first.")
        return
    parts = message.text.split() if message.text else []
    if len(parts) != 5:
        await message.answer(f"Usage: /paper{'buy' if side == 'BUY' else 'sell'} <market_pair_id> <strategy_id> <quantity> <price>")
        return
    _, market_pair_id, strategy_id, quantity, price = parts
    try:
        result = await backend.post(
            "/trading/paper-orders",
            {
                "market_pair_id": market_pair_id,
                "strategy_id": strategy_id,
                "side": side,
                "quantity": float(quantity),
                "price": float(price),
            },
            token=token,
        )
        await message.answer(
            f"Paper {side} result: {result.get('message')}\n"
            f"Risk: {result.get('risk_reason')}\n"
            f"Order: {result.get('order', {}).get('status') if isinstance(result.get('order'), dict) else 'n/a'}"
        )
    except Exception as exc:
        await message.answer(f"Paper order failed: {exc}")
