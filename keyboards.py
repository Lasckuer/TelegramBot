from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    buttons = [
        [KeyboardButton(text="Расходы"), KeyboardButton(text="Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_expenses_menu():
    buttons = [
        [KeyboardButton(text="Внести расход"), KeyboardButton(text="Удалить запись")],
        [KeyboardButton(text="Отсканировать чек"), KeyboardButton(text="Поиск")],
        # Добавили кнопку Сравнение
        [KeyboardButton(text="Отчеты"), KeyboardButton(text="Сравнение")], 
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_settings_menu():
    buttons = [
        [KeyboardButton(text="Экспорт"), KeyboardButton(text="График")],
        [KeyboardButton(text="Лимиты"), KeyboardButton(text="Уведомления")],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_categories_kb():
    buttons = [
        [KeyboardButton(text="Продукты"), KeyboardButton(text="Развлечения")],
        [KeyboardButton(text="Ежемесячные"), KeyboardButton(text="Остальное")],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_cancel_kb():
    buttons = [[KeyboardButton(text="Назад")]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_pagination_kb(page: int, total_pages: int):
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{page-1}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"page_{page+1}"))
    
    if buttons:
        return InlineKeyboardMarkup(inline_keyboard=[buttons])
    return None