from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.keyboards.inline.menus import get_pagination_keyboard
from app.handlers.utils import db

router = Router()

@router.callback_query(F.data.startswith("exp_page_"))
async def show_expenses_list(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    limit = 10
    offset = page * limit
    
    user_id = callback.from_user.id
    
    items = db.get_expenses_paginated(user_id, limit=limit, offset=offset)
    
    next_items = db.get_expenses_paginated(user_id, limit=1, offset=offset + limit)
    has_next = len(next_items) > 0

    if not items and page == 0:
        return await callback.answer("У вас пока нет записанных расходов.", show_alert=True)

    text = f"📋 <b>Список расходов (Страница {page + 1}):</b>\n"
    text += "⎯" * 15 + "\n"
    
    for i, item in enumerate(items, offset + 1):
        text += f"{i}. <b>{item['name']}</b>: <code>{item['price']}₽</code>\n"
        text += f"└ <i>{item['date']}</i>\n\n"

    kb = get_pagination_keyboard(page, has_next)
    
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    
    await callback.answer()