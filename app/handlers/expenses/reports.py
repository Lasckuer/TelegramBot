from aiogram import Router, F, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from app.keyboards.inline.menus import get_inline_expenses_menu
from app.keyboards.inline.categories import get_inline_categories_kb
from app.handlers.utils import db

router = Router()

def get_report_pagination_kb(page: int, has_next: bool, category: str = None):
    buttons = []
    nav_row = []
    cat_prefix = f"{category}_" if category else "None_"
    
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"exp_page_{cat_prefix}{page-1}"))
    if has_next:
        nav_row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"exp_page_{cat_prefix}{page+1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="select_exp_list_cat")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(F.data == "select_exp_list_cat")
async def select_category_for_list(callback: CallbackQuery):
    kb = get_inline_categories_kb("listcat")
    kb.inline_keyboard.append([InlineKeyboardButton(text="📊 Все расходы", callback_data="listcat_Все")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")])
    await callback.message.edit_text(
        "Выберите категорию для просмотра истории:", 
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(F.data.startswith("listcat_") | F.data.startswith("exp_page_"))
async def show_expenses_list(callback: CallbackQuery):
    data = callback.data.split("_")
    
    if callback.data.startswith("listcat_"):
        category = data[1] if data[1] != "Все" else None
        page = 0
    else:
        category = data[2] if data[2] != "None" else None
        page = int(data[3])

    limit = 10
    offset = page * limit
    user_id = callback.from_user.id
    
    items = db.get_expenses_paginated(user_id, category=category, limit=limit, offset=offset)
    
    if not items and page == 0:
        return await callback.answer(f"В категории {category or 'Все'} нет записей.", show_alert=True)

    text = f"📋 <b>{category or 'Все расходы'}</b> (Стр. {page + 1})\n"
    text += "⎯" * 15 + "\n"
    
    for i, item in enumerate(items, offset + 1):
        cur = "₽" if item.get('currency') == "RUB" else item.get('currency', '₽')
        text += f"{i}. <b>{item['name']}</b>: <code>{item['price']}{cur}</code>\n"
        text += f"└ <i>{item['date']}</i>\n\n"

    kb = get_report_pagination_kb(page, len(items) == limit, category)
    
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def process_back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "<b>Управление расходами:</b>",
        reply_markup=get_inline_expenses_menu(),
        parse_mode="HTML"
    )
    await callback.answer()