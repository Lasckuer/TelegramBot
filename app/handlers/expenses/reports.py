from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.keyboards.inline.menus import get_pagination_keyboard
from app.keyboards.inline.categories import get_inline_categories_kb #
from app.handlers.utils import db

router = Router()

@router.callback_query(F.data == "select_exp_list_cat")
async def select_category_for_list(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите категорию для просмотра или покажите всё:", 
        reply_markup=get_inline_categories_kb("listcat")
    )

@router.callback_query(F.data.startswith("listcat_") | F.data.startswith("exp_page_"))
async def show_expenses_list(callback: CallbackQuery):
    if callback.data.startswith("listcat_"):
        category = callback.data.split("_")[1]
        page = 0
    else:
        parts = callback.data.split("_")
        category = parts[2] if len(parts) > 3 else None
        page = int(parts[-1])

    limit = 10
    offset = page * limit
    user_id = callback.from_user.id
    
    items = db.get_expenses_paginated(user_id, category=category, limit=limit, offset=offset)
    
    if not items and page == 0:
        return await callback.answer("В этой категории пока нет записей.", show_alert=True)

    text = f"📋 <b>Список: {category or 'Все'} (Стр. {page + 1})</b>\n"
    text += "⎯" * 15 + "\n"
    
    for i, item in enumerate(items, offset + 1):
        cur = "₽" if item['currency'] == "RUB" else item['currency']
        text += f"{i}. <b>{item['name']}</b>: <code>{item['price']}{cur}</code>\n"
        text += f"└ <i>{item['date']}</i>\n\n"

    has_next = len(items) == limit
    kb = get_pagination_keyboard(page, has_next) #
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()