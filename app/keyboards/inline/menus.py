from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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
         InlineKeyboardButton(text="🤖 AI Советы", callback_data="menu_ai_tips")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_inline_settings_menu():
    buttons = [
        [InlineKeyboardButton(text="🎯 Лимиты", callback_data="menu_limits"),
         InlineKeyboardButton(text="🔔 Уведомления", callback_data="menu_notifications")],
        [InlineKeyboardButton(text="📥 Экспорт в Excel", callback_data="menu_export")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)