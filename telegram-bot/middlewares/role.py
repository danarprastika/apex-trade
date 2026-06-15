from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class RoleMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        return await handler(event, data)
