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
        [InlineKeyboardButton(text="📈 График расходов", callback_data="menu_chart"),
         InlineKeyboardButton(text="🗓 Сравнение", callback_data="menu_compare")]
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