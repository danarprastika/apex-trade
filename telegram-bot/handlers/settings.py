from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from clients.backend import BackendClient
from services.token_store import token_store

router = Router()
backend = BackendClient()


@router.callback_query(lambda query: query.data == "settings")
async def settings_callback(query: CallbackQuery):
    await settings_message(query.message)
    await query.answer()


@router.message(Command("settings"))
async def settings_message(message: Message):
    token = token_store.get(message.chat.id)
    if not token:
        await message.answer("Run /auth <access_token> first, then use /settings.")
        return
    try:
        settings = await backend.get("/users/me/settings", token=token)
        await message.answer(
            "Settings\n"
            f"Timezone: {settings.get('timezone')}\n"
            f"Language: {settings.get('language')}\n"
            f"Theme: {settings.get('theme')}\n"
            f"Telegram Chat ID: {settings.get('telegram_chat_id') or 'not linked'}"
        )
    except Exception as exc:
        await message.answer(f"Failed to load settings: {exc}")


@router.message(Command("link"))
async def link_command(message: Message):
    token = token_store.get(message.chat.id)
    if not token:
        await message.answer("Run /auth <access_token> first.")
        return
    try:
        await backend.post("/users/me/settings/telegram", {"telegram_chat_id": str(message.chat.id)}, token=token)
        await message.answer(f"Linked Telegram chat {message.chat.id} to APEX.")
    except Exception as exc:
        await message.answer(f"Failed to link Telegram: {exc}")
