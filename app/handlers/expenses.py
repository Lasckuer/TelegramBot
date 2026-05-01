import math
import os
from aiogram import Router, F, Bot, types
from aiogram.fsm.context import FSMContext
import keyboards.inline as kb_inline
import keyboards.reply as kb_reply
from states import ExpenseForm, SearchState, EditState
from gsheets import GoogleTable
from qr_scanner import decode_qr, fetch_receipt_data
import aiohttp
from .common import main_menu
from utils import load_cat_map, save_cat_map, generate_page_text

router = Router()
db = GoogleTable()
LIMIT = 50000
        
# ==========================================
# --- РАСХОДЫ ---
# ==========================================
@router.callback_query(F.data == "menu_add_exp")
async def start_expense(callback: types.CallbackQuery):
    await callback.message.edit_text("Выбери категорию:", reply_markup=kb_inline.get_inline_categories_kb("addcat"))
    await callback.answer()

@router.callback_query(F.data.startswith("addcat_"))
async def select_category_inline(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[1]
    await state.set_state(ExpenseForm.category)
    await state.update_data(category=category)
    await state.set_state(ExpenseForm.name)
    await callback.message.delete()
    await callback.message.answer(f"Внесение расхода в <b>{category}</b>.\nВведите название:", parse_mode="HTML", reply_markup=kb_reply.get_cancel_kb())
    await callback.answer()

@router.message(ExpenseForm.name)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)
    await state.update_data(name=message.text)
    await state.set_state(ExpenseForm.price)
    await message.answer("Введите стоимость:")

@router.message(ExpenseForm.price)
async def process_price(message: types.Message, state: FSMContext):
    text = message.text.lower()
    is_usd = False
    
    if '$' in text or 'usd' in text:
        is_usd = True
        text = text.replace('$', '').replace('usd', '').strip()
        
    if not text.replace('.', '', 1).isdigit():
        return await message.answer("Введите только число (можно с $):")
        
    amount = float(text)
    
    if is_usd:
        msg = await message.answer("🔄 Конвертирую по актуальному курсу...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.exchangerate-api.com/v4/latest/USD") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        rate = data['rates'].get('RUB', 90)
                        amount = math.ceil(amount * rate)
        except Exception:
            amount = math.ceil(amount * 90)
        await msg.delete()
        
    if amount > LIMIT:
        await message.answer(f"⚠️ Внимание! Трата превышает ваш лимит {LIMIT}р!")
        
    await state.update_data(price=str(int(amount)))
    await state.set_state(ExpenseForm.shop)
    await message.answer(f"Сумма: {int(amount)}р.\nМагазин (или 'нет'):")

@router.message(ExpenseForm.shop)
async def process_shop(message: types.Message, state: FSMContext):
    data = await state.get_data()
    shop = message.text if message.text.lower() != 'нет' else "-"
    db.add_expense(data['category'], data['name'], data['price'], shop)
    
    if shop != "-":
        cmap = load_cat_map()
        cmap[shop.lower().strip()] = data['category']
        save_cat_map(cmap)
        
    await message.answer("✅ Записано!", reply_markup=kb_reply.get_main_menu())
    await state.clear()

@router.callback_query(F.data == "menu_scan_exp")
async def ask_for_receipt(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Отправь мне фотографию QR-кода с чека (без сжатия или крупным планом).", reply_markup=kb_reply.get_cancel_kb())
    await callback.answer()

@router.message(F.photo)
async def handle_receipt_photo(message: types.Message, bot: Bot):
    await message.answer("⏳ Анализирую QR-код...")
    photo = message.photo[-1]
    file_path = f"temp_{photo.file_id}.jpg"
    await bot.download(photo, destination=file_path)
    
    qr_string = decode_qr(file_path)
    if os.path.exists(file_path):
        os.remove(file_path) 
    
    if not qr_string:
        return await message.answer("❌ QR-код не найден.", reply_markup=kb_reply.get_main_menu())
    
    await message.answer("🔍 Запрашиваю данные из ФНС...")
    
    try:
        receipt_data = await fetch_receipt_data(qr_string)
        if not receipt_data or receipt_data.get('code') != 1:
            return await message.answer("❌ Ошибка получения данных чека.", reply_markup=kb_reply.get_main_menu())
        
        items = receipt_data['data']['json']['items']
        added_count = 0
        total_sum = 0
        shop_name = receipt_data['data']['json'].get('user') or receipt_data['data']['json'].get('retailPlace', 'Магазин из чека')
        
        cmap = load_cat_map()
        assigned_cat = cmap.get(shop_name.lower().strip(), "Продукты")
        
        for item in items:
            name = item.get('name', 'Неизвестный товар')
            price = math.ceil(int(item.get('sum', 0)) / 100)
            
            db.add_expense(category=assigned_cat, name=name, price=price, shop=shop_name)
            added_count += 1
            total_sum += price
            
        await message.answer(f"✅ Добавлено {added_count} позиций (Категория: {assigned_cat}).\nНа сумму: {total_sum}р.", reply_markup=kb_reply.get_main_menu())
        
    except Exception:
        await message.answer("❌ Произошла ошибка при обработке.", reply_markup=kb_reply.get_main_menu())

@router.callback_query(F.data == "menu_search_exp")
async def search_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Введите название товара или магазина для поиска:", reply_markup=kb_reply.get_cancel_kb())
    await state.set_state(SearchState.waiting_for_query)
    await callback.answer()

@router.message(SearchState.waiting_for_query)
async def search_process(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)

    df = db.get_all_df()
    if df.empty:
        await message.answer("Таблица расходов пока пуста.", reply_markup=kb_reply.get_main_menu())
        return await state.clear()

    query = message.text.lower()
    if 'Название' not in df.columns: df['Название'] = ""
    if 'Магазин' not in df.columns: df['Магазин'] = ""

    result = df[
        df['Название'].astype(str).str.lower().str.contains(query, na=False) | 
        df['Магазин'].astype(str).str.lower().str.contains(query, na=False)
    ]
    
    if result.empty:
        await message.answer("Ничего не найдено.", reply_markup=kb_reply.get_main_menu())
        return await state.clear()
    
    matches = result.to_dict('records')
    await state.update_data(search_results=matches, query=query)
    
    text, markup = generate_page_text(matches, query, page=0)
    await message.answer(text, reply_markup=markup, parse_mode="HTML")

@router.callback_query(F.data.startswith("page_"))
async def process_page_callback(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])
    
    data = await state.get_data()
    matches = data.get("search_results", [])
    query = data.get("query", "")

    if not matches:
        return await callback.answer("Данные устарели. Сделайте поиск заново.", show_alert=True)

    text, markup = generate_page_text(matches, query, page)
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "menu_manage_exp")
async def start_manage_inline(callback: types.CallbackQuery):
    await callback.message.edit_text("В какой категории?", reply_markup=kb_inline.get_inline_categories_kb("mngcat"))
    await callback.answer()

@router.callback_query(F.data.startswith("mngcat_"))
async def show_items_to_manage(callback: types.CallbackQuery):
    category = callback.data.split("_")[1]
    items = db.get_records_by_category(category)
    if not items:
        return await callback.message.edit_text(f"В категории «{category}» пусто.")
    await callback.message.edit_text(f"Последние записи ({category}):", reply_markup=kb_inline.get_inline_manage_items_kb(items))

@router.callback_query(F.data.startswith("manageitem_"))
async def item_actions_inline(callback: types.CallbackQuery):
    row_idx = int(callback.data.split("_")[1])
    await callback.message.edit_text("Что сделать с записью?", reply_markup=kb_inline.get_inline_item_action_kb(row_idx))

@router.callback_query(F.data.startswith("delconfirm_"))
async def execute_delete_inline(callback: types.CallbackQuery):
    row_idx = int(callback.data.split("_")[1])
    db.delete_by_row(row_idx)
    await callback.message.edit_text("✅ Запись удалена.")

@router.callback_query(F.data == "delcancel")
async def cancel_manage_inline(callback: types.CallbackQuery):
    await callback.message.edit_text("Действие отменено.")

@router.callback_query(F.data.startswith("editname_"))
async def edit_name_start(callback: types.CallbackQuery, state: FSMContext):
    row_idx = int(callback.data.split("_")[1])
    await state.update_data(edit_row=row_idx)
    await state.set_state(EditState.waiting_for_new_name)
    await callback.message.delete()
    await callback.message.answer("Введите новое название:", reply_markup=kb_reply.get_cancel_kb())
    await callback.answer()

@router.message(EditState.waiting_for_new_name)
async def edit_name_process(message: types.Message, state: FSMContext):
    data = await state.get_data()
    db.update_cell(data['edit_row'], 2, message.text)
    await message.answer("✅ Название обновлено!", reply_markup=kb_reply.get_main_menu())
    await state.clear()
    
@router.callback_query(F.data.startswith("editprice_"))
async def edit_price_start(callback: types.CallbackQuery, state: FSMContext):
    row_idx = int(callback.data.split("_")[1])
    await state.update_data(edit_row=row_idx)
    await state.set_state(EditState.waiting_for_new_price)
    await callback.message.delete()
    await callback.message.answer("Введите новую цену:", reply_markup=kb_reply.get_cancel_kb())
    await callback.answer()

@router.message(EditState.waiting_for_new_price)
async def edit_price_process(message: types.Message, state: FSMContext):
    data = await state.get_data()
    db.update_cell(data['edit_row'], 3, int(message.text))
    await message.answer("✅ Цена обновлена!", reply_markup=kb_reply.get_main_menu())
    await state.clear()