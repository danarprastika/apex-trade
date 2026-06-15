from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from clients.backend import BackendClient
from services.token_store import token_store

router = Router()
backend = BackendClient()


@router.message(Command("admin"))
async def admin_message(message: Message):
    token = token_store.get(message.chat.id)
    if not token:
        await message.answer("Run /auth <access_token> first.")
        return
    try:
        system = await backend.get("/admin/system", token=token)
        audit = await backend.get("/admin/audit", token=token)
        await message.answer(f"Admin system: {system}\nAudit logs: {len(audit)}")
    except Exception as exc:
        await message.answer(f"Admin access denied: {exc}")
