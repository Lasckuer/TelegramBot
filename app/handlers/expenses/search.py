from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
import app.keyboards.reply as kb_reply
from app.states import SearchState
from app.database.db_manager import DatabaseManager
from app.handlers.common.base import main_menu
from app.handlers.utils import generate_page_text

router = Router()
db = DatabaseManager()

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

    user_id = message.from_user.id
    df = db.get_all_df(user_id)
    
    if df.empty:
        await message.answer("Таблица расходов пока пуста.", reply_markup=kb_reply.get_main_menu())
        return await state.clear()

    query = message.text.lower()
    result = df[
        df['name'].astype(str).str.lower().str.contains(query, na=False) | 
        df['shop'].astype(str).str.lower().str.contains(query, na=False)
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