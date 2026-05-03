import calendar
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_inline_expenses_menu():
    buttons = [
        [InlineKeyboardButton(text="✍️ Внести вручную", callback_data="menu_add_exp"),
         InlineKeyboardButton(text="🧾 Скан чека", callback_data="menu_scan_exp")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="menu_search_exp"),
         InlineKeyboardButton(text="✏️ Управление", callback_data="menu_manage_exp")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_inline_incomes_menu():
    buttons = [
        [InlineKeyboardButton(text="➕ Внести доход", callback_data="menu_add_inc"),
         InlineKeyboardButton(text="✏️ Управление", callback_data="menu_manage_inc")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_inline_analytics_menu():
    buttons = [
        [InlineKeyboardButton(text="⚖️ Баланс месяца", callback_data="menu_balance")],
        [InlineKeyboardButton(text="📈 Тренд", callback_data="menu_trend"),
         InlineKeyboardButton(text="🗓 Сравнение", callback_data="menu_compare")],
        [InlineKeyboardButton(text="💼 Портфель", callback_data="menu_portfolio"),
         InlineKeyboardButton(text="🤖 AI Советы", callback_data="menu_ai_tips")] # Новая кнопка
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_inline_settings_menu():
    buttons = [
        [InlineKeyboardButton(text="🎯 Лимиты", callback_data="menu_limits"),
         InlineKeyboardButton(text="🔔 Уведомления", callback_data="menu_notifications")],
        [InlineKeyboardButton(text="📥 Экспорт в Excel", callback_data="menu_export")]
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

def get_inline_income_categories_kb(prefix: str):
    buttons = [
        [InlineKeyboardButton(text="Зарплата", callback_data=f"{prefix}_Зарплата"),
         InlineKeyboardButton(text="Фриланс", callback_data=f"{prefix}_Фриланс")],
        [InlineKeyboardButton(text="Кэшбэк/Бонусы", callback_data=f"{prefix}_Кэшбэк"),
         InlineKeyboardButton(text="Переводы", callback_data=f"{prefix}_Переводы")],
        [InlineKeyboardButton(text="Остальное", callback_data=f"{prefix}_Остальное")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_pagination_kb(page: int, total_pages: int):
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{page-1}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"page_{page+1}"))
    if buttons:
        return InlineKeyboardMarkup(inline_keyboard=[buttons])
    return None

def get_inline_manage_items_kb(items: list, prefix: str = "manageitem"):
    builder = InlineKeyboardBuilder()
    for item in items:
        text = f"{item.get('Название', '???')} — {item.get('Стоимость', 0)}р"
        row_idx = item.get('row_idx')
        builder.row(InlineKeyboardButton(text=text, callback_data=f"{prefix}_{row_idx}"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="delcancel"))
    return builder.as_markup()

def get_inline_item_action_kb(row_idx: int, prefix: str = "exp"):
    is_income = prefix.startswith("inc")
    label_name = "✏️ Источник" if is_income else "✏️ Название"
    label_price = "✏️ Сумму" if is_income else "✏️ Цену"
    buttons = [
        [InlineKeyboardButton(text=label_name, callback_data=f"{prefix}editname_{row_idx}"),
         InlineKeyboardButton(text=label_price, callback_data=f"{prefix}editprice_{row_idx}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"{prefix}delconfirm_{row_idx}")],
        [InlineKeyboardButton(text="❌ Назад", callback_data="delcancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_inline_debts_menu():
    buttons = [
        [InlineKeyboardButton(text="➕ Дать в долг", callback_data="menu_add_debt"),
         InlineKeyboardButton(text="📋 Активные долги", callback_data="menu_list_debts")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_inline_sub_action_kb(sub_idx: int):
    buttons = [
        [InlineKeyboardButton(text="✅ Списать", callback_data=f"subpay_{sub_idx}"),
         InlineKeyboardButton(text="❌ Отмена", callback_data=f"subcancel_{sub_idx}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_inline_debt_return_kb(debt_id: str):
    buttons = [
        [InlineKeyboardButton(text="💸 Вернул!", callback_data=f"debtret_{debt_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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

