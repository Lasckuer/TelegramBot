from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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