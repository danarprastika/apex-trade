from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from clients.backend import BackendClient
from services.token_store import token_store

router = Router()
backend = BackendClient()


@router.message(Command("accounts"))
async def accounts_message(message: Message):
    token = token_store.get(message.chat.id)
    if not token:
        await message.answer("Run /auth <access_token> first.")
        return
    try:
        accounts = await backend.get("/exchanges/accounts", token=token)
        if not accounts:
            await message.answer("No exchange accounts found.")
            return
        lines = [
            f"{account.get('id')} {account.get('exchange_id')} sync={account.get('sync_status')} status={account.get('status')}"
            for account in accounts
        ]
        await message.answer("Exchange accounts:\n" + "\n".join(lines))
    except Exception as exc:
        await message.answer(f"Failed to load exchange accounts: {exc}")


@router.message(Command("sync"))
async def sync_command(message: Message):
    token = token_store.get(message.chat.id)
    if not token:
        await message.answer("Run /auth <access_token> first.")
        return
    parts = message.text.split() if message.text else []
    if len(parts) != 2:
        await message.answer("Usage: /sync <account_id>")
        return
    account_id = parts[1]
    try:
        result = await backend.post(f"/exchanges/accounts/{account_id}/sync", {}, token=token)
        balances = result.get("balances", {}).get("currencies", [])
        await message.answer(f"Synced {account_id}\nBalances: {len(balances)} currencies")
    except Exception as exc:
        await message.answer(f"Sync failed: {exc}")
