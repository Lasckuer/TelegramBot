import calendar
from datetime import datetime
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    buttons = [
        [KeyboardButton(text="💸 Расходы"), KeyboardButton(text="💰 Доходы")],
        [KeyboardButton(text="📊 Аналитика"), KeyboardButton(text="⚙️ Настройки")],
        [KeyboardButton(text="🤝 Долги")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Кнопка отмены для состояний ввода текста (оставляем обычную)
def get_cancel_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True)