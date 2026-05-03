import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
ADMIN_ID = str(os.getenv("ADMIN_ID", "0"))

def get_inline_expenses_menu():
    buttons = [
        [InlineKeyboardButton(text="✍️ Внести вручную", callback_data="menu_add_exp"),
         InlineKeyboardButton(text="🧾 Скан чека", callback_data="menu_scan_exp")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="menu_search_exp"),
         InlineKeyboardButton(text="✏️ Управление", callback_data="menu_manage_exp")],
        [InlineKeyboardButton(text="📜 История расходов", callback_data="exp_page_0")]
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

def get_inline_settings_menu(user_id: int):
    buttons = [
        [InlineKeyboardButton(text="🎯 Лимиты", callback_data="menu_limits"),
         InlineKeyboardButton(text="🔔 Уведомления", callback_data="menu_notifications")],
        [InlineKeyboardButton(text="📥 Экспорт в Excel", callback_data="menu_export")]
    ]
    if str(user_id) == ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="Админ-панель", callback_data="open_admin_panel")])
        
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_panel_kb():
    buttons = [
        [InlineKeyboardButton(text="🛠 Тех. работы", callback_data="admin_tech_toggle")],
        [InlineKeyboardButton(text="📝 Логи (Хвост)", callback_data="admin_logs")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📊 Статус системы", callback_data="admin_stats")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_cancel_broadcast_kb():
    buttons = [
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_broadcast")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_pagination_keyboard(page: int, has_next: bool):
    buttons = []
    nav_row = []
    
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"exp_page_{page-1}"))
    if has_next:
        nav_row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"exp_page_{page+1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    buttons.append([InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)