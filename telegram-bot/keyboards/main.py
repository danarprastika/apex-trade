from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Status", callback_data="status")],
        [InlineKeyboardButton(text="Portfolio", callback_data="portfolio")],
        [InlineKeyboardButton(text="Signals", callback_data="signals")],
        [InlineKeyboardButton(text="Risk", callback_data="risk")],
        [InlineKeyboardButton(text="Settings", callback_data="settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
