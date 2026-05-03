from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

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