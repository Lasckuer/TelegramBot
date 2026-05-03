import calendar
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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