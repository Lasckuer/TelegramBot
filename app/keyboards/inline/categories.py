from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_inline_categories_kb(prefix: str):
    buttons = [
        [InlineKeyboardButton(text="Продукты", callback_data=f"{prefix}_Продукты"),
         InlineKeyboardButton(text="Развлечения", callback_data=f"{prefix}_Развлечения")],
        [InlineKeyboardButton(text="Ежемесячные", callback_data=f"{prefix}_Ежемесячные"),
         InlineKeyboardButton(text="Остальное", callback_data=f"{prefix}_Остальное")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_inline_income_categories_kb(prefix: str):
    buttons = [
        [InlineKeyboardButton(text="Зарплата", callback_data=f"{prefix}_Зарплата"),
         InlineKeyboardButton(text="Фриланс", callback_data=f"{prefix}_Фриланс")],
        [InlineKeyboardButton(text="Кэшбэк/Бонусы", callback_data=f"{prefix}_Кэшбэк"),
         InlineKeyboardButton(text="Переводы", callback_data=f"{prefix}_Переводы")],
        [InlineKeyboardButton(text="Остальное", callback_data=f"{prefix}_Остальное")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)