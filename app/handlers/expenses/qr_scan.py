import os
import math
from aiogram import Router, F, Bot, types
from aiogram.fsm.context import FSMContext
import app.keyboards.reply as kb_reply
from app.database.db_manager import DatabaseManager
from app.handlers.qr_scanner import decode_qr, fetch_receipt_data
from app.handlers.utils import load_cat_map

router = Router()
db = DatabaseManager()

@router.callback_query(F.data == "menu_scan_exp")
async def ask_for_receipt(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "Отправь мне фотографию QR-кода с чека.", 
        reply_markup=kb_reply.get_cancel_kb()
    )
    await callback.answer()

@router.message(F.photo)
async def handle_receipt_photo(message: types.Message, bot: Bot):
    status_msg = await message.answer("⌛ Обрабатываю фото...")
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    photo = message.photo[-1]
    file_path = f"temp_{photo.file_id}.jpg"
    await bot.download(photo, destination=file_path)
    
    try:
        qr_string = await decode_qr(file_path)
        
        if os.path.exists(file_path):
            os.remove(file_path) 
        
        if not qr_string:
            return await status_msg.edit_text("❌ QR-код не найден. Попробуйте еще раз.")
        
        await status_msg.edit_text("🔍 Запрашиваю данные из ФНС...")
        receipt_data = await fetch_receipt_data(qr_string)
        
        if not receipt_data or receipt_data.get('code') != 1:
            error_info = receipt_data.get('data', "Ошибка получения данных") if receipt_data else "API не ответил"
            return await status_msg.edit_text(f"❌ {error_info}")
        
        items = receipt_data['data']['json']['items']
        user_id = message.from_user.id
        shop_name = receipt_data['data']['json'].get('user') or receipt_data['data']['json'].get('retailPlace', 'Магазин')
        
        cmap = load_cat_map()
        assigned_cat = cmap.get(shop_name.lower().strip(), "Продукты")
        
        total_sum = 0
        for item in items:
            name = item.get('name', 'Товар')
            price = math.ceil(int(item.get('sum', 0)) / 100)
            db.add_expense(user_id=user_id, category=assigned_cat, name=name, price=price, shop=shop_name)
            total_sum += price
            
        await status_msg.delete()
        await message.answer(
            f"✅ Добавлено товаров: {len(items)}\nКатегория: {assigned_cat}\nИтог: {total_sum}р.", 
            reply_markup=kb_reply.get_main_menu()
        )
        
    except Exception as e:
        if os.path.exists(file_path): 
            os.remove(file_path)
        await message.answer("❌ Ошибка при обработке.", reply_markup=kb_reply.get_main_menu())
        print(f"QR Error: {e}")