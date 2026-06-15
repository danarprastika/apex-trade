from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from clients.backend import BackendClient
from keyboards.main import main_menu
from services.token_store import token_store

router = Router()
backend = BackendClient()


@router.message(Command("start"))
async def start(message: Message):
    await message.answer("Welcome to APEX. Choose an action:", reply_markup=main_menu())


@router.callback_query(lambda query: query.data == "status")
async def status_callback(query: CallbackQuery):
    await status_message(query.message)
    await query.answer()


@router.message(Command("status"))
async def status_message(message: Message):
    try:
        health = await backend.get("/health")
        await message.answer(f"Backend status: {health.get('status')}", reply_markup=main_menu())
    except Exception as exc:
        await message.answer(f"Backend status failed: {exc}", reply_markup=main_menu())


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "Available commands:\n"
        "/auth <token> - link this Telegram chat to your APEX account\n"
        "/unlink - remove the stored token\n"
        "/status - backend health\n"
        "/portfolio - portfolio summary\n"
        "/risk - risk profile and decision metrics\n"
        "/accounts - exchange accounts\n"
        "/sync <account_id> - sync exchange balances\n"
        "/signals - latest signals\n"
        "/orders - latest orders"
    )


@router.message(Command("auth"))
async def auth_command(message: Message):
    token = message.text.split(maxsplit=1)[1].strip() if message.text and len(message.text.split(maxsplit=1)) > 1 else ""
    if not token:
        await message.answer("Usage: /auth <access_token>")
        return
    try:
        user = await backend.get("/users/me", token=token)
        token_store.save(message.chat.id, token)
        await message.answer(f"Telegram linked for {user['username']} ({user['role']}).")
    except Exception as exc:
        await message.answer(f"Failed to link Telegram: {exc}")


@router.message(Command("unlink"))
async def unlink_command(message: Message):
    token_store.delete(message.chat.id)
    await message.answer("Telegram chat unlinked from APEX.")
