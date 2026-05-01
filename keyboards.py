# ==========================================
# --- KEYBOARDS.PY ---
# ==========================================
import calendar
from datetime import datetime
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    buttons = [
        [KeyboardButton(text="Расходы"), KeyboardButton(text="Доходы")],
        [KeyboardButton(text="Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_expenses_menu():
    buttons = [
        [KeyboardButton(text="Внести расход"), KeyboardButton(text="Управление")],
        [KeyboardButton(text="Отсканировать чек"), KeyboardButton(text="Поиск")],
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

def get_calendar_kb(year: int = None, month: int = None):
    if year is None or month is None:
        now = datetime.now()
        year, month = now.year, now.month

    keyboard = []
    
    month_names = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    keyboard.append([InlineKeyboardButton(text=f"{month_names[month]} {year}", callback_data="calendar_ignore")])

    days_of_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    keyboard.append([InlineKeyboardButton(text=day, callback_data="calendar_ignore") for day in days_of_week])

    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="calendar_ignore"))
            else:
                row.append(InlineKeyboardButton(text=str(day), callback_data=f"calendar_day_{year}_{month}_{day}"))
        keyboard.append(row)

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    keyboard.append([
        InlineKeyboardButton(text="<", callback_data=f"calendar_nav_{prev_year}_{prev_month}"),
        InlineKeyboardButton(text="Отмена", callback_data="calendar_cancel"),
        InlineKeyboardButton(text=">", callback_data=f"calendar_nav_{next_year}_{next_month}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_incomes_menu():
    buttons = [
        [KeyboardButton(text="Внести доход")],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_inline_income_categories_kb(prefix: str):
    buttons = [
        [InlineKeyboardButton(text="Зарплата", callback_data=f"{prefix}_Зарплата"),
         InlineKeyboardButton(text="Фриланс", callback_data=f"{prefix}_Фриланс")],
        [InlineKeyboardButton(text="Кэшбэк/Бонусы", callback_data=f"{prefix}_Кэшбэк"),
         InlineKeyboardButton(text="Переводы", callback_data=f"{prefix}_Переводы")],
        [InlineKeyboardButton(text="Остальное", callback_data=f"{prefix}_Остальное")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_inline_categories_kb(prefix: str):
    buttons = [
        [InlineKeyboardButton(text="Продукты", callback_data=f"{prefix}_Продукты"),
         InlineKeyboardButton(text="Развлечения", callback_data=f"{prefix}_Развлечения")],
        [InlineKeyboardButton(text="Ежемесячные", callback_data=f"{prefix}_Ежемесячные"),
         InlineKeyboardButton(text="Остальное", callback_data=f"{prefix}_Остальное")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_inline_delete_items_kb(items: list):
    buttons = []
    for item in items:
        text = f"{item.get('Название', 'Без названия')} — {item.get('Стоимость', 0)}р"
        row_idx = item.get('row_idx')
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"delitem_{row_idx}")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="delcancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_inline_confirm_kb(row_idx: int):
    buttons = [
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"delconfirm_{row_idx}"),
         InlineKeyboardButton(text="❌ Отмена", callback_data="delcancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_inline_manage_items_kb(items: list):
    buttons = []
    for item in items:
        text = f"{item.get('Название', 'Без названия')} — {item.get('Стоимость', 0)}р"
        row_idx = item.get('row_idx')
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"manageitem_{row_idx}")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="delcancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_inline_item_action_kb(row_idx: int):
    buttons = [
        [InlineKeyboardButton(text="✏️ Название", callback_data=f"editname_{row_idx}"),
         InlineKeyboardButton(text="✏️ Цену", callback_data=f"editprice_{row_idx}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delconfirm_{row_idx}")],
        [InlineKeyboardButton(text="❌ Назад", callback_data="delcancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)