from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from clients.backend import BackendClient
from keyboards.main import main_menu
from services.formatters import format_money, format_percent
from services.token_store import token_store

router = Router()
backend = BackendClient()


@router.callback_query(lambda query: query.data == "portfolio")
async def portfolio_callback(query: CallbackQuery):
    await portfolio_message(query.message)
    await query.answer()


@router.message(Command("portfolio"))
async def portfolio_message(message: Message):
    token = token_store.get(message.chat.id)
    if not token:
        await message.answer("Run /auth <access_token> first.")
        return
    try:
        portfolio = await backend.get("/portfolio", token=token)
        text = (
            "Portfolio summary\n"
            f"Total Value: {format_money(float(portfolio.get('total_value') or 0))}\n"
            f"Cash: {format_money(float(portfolio.get('cash_balance') or 0))}\n"
            f"Risk Score: {format_percent(float(portfolio.get('risk_score') or 0))}"
        )
        await message.answer(text, reply_markup=main_menu())
    except Exception as exc:
        await message.answer(f"Failed to load portfolio: {exc}")


@router.message(Command("balance"))
async def balance_message(message: Message):
    token = token_store.get(message.chat.id)
    if not token:
        await message.answer("Run /auth <access_token> first.")
        return
    try:
        portfolio = await backend.get("/portfolio", token=token)
        await message.answer(f"Balance: {format_money(float(portfolio.get('cash_balance') or 0))}")
    except Exception as exc:
        await message.answer(f"Failed to load balance: {exc}")
