from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
import app.keyboards.inline as kb_inline
import app.keyboards.reply as kb_reply
from app.states import EditExpState
from app.database.db_manager import DatabaseManager

router = Router()
db = DatabaseManager()

@router.callback_query(F.data == "menu_manage_exp")
async def start_manage_inline(callback: types.CallbackQuery):
    await callback.message.edit_text("В какой категории?", reply_markup=kb_inline.get_inline_categories_kb("mngcat"))
    await callback.answer()

@router.callback_query(F.data.startswith("mngcat_"))
async def show_items_to_manage(callback: types.CallbackQuery):
    category = callback.data.split("_")[1]
    items = db.get_records_by_category(category, callback.from_user.id) 
    if not items:
        return await callback.message.edit_text(f"В категории «{category}» пусто.")
    await callback.message.edit_text(f"Последние записи ({category}):", reply_markup=kb_inline.get_inline_manage_items_kb(items))

@router.callback_query(F.data.startswith("manageitem_"))
async def item_actions_inline(callback: types.CallbackQuery):
    row_idx = int(callback.data.split("_")[1])
    await callback.message.edit_text("Что сделать с записью?", reply_markup=kb_inline.get_inline_item_action_kb(row_idx, prefix="exp"))


@router.callback_query(F.data.startswith("expdelconfirm_"))
async def execute_delete_inline(callback: types.CallbackQuery):
    row_idx = int(callback.data.split("_")[1])
    db.delete_by_row(row_idx, callback.from_user.id) 
    await callback.message.edit_text("✅ Запись удалена.")

@router.callback_query(F.data.startswith("expeditname_"))
async def edit_name_start(callback: types.CallbackQuery, state: FSMContext):
    row_idx = int(callback.data.split("_")[1])
    await state.update_data(edit_row=row_idx)
    await state.set_state(EditExpState.waiting_for_new_name)
    await callback.message.delete()
    await callback.message.answer("Введите новое название:", reply_markup=kb_reply.get_cancel_kb())
    await callback.answer()

@router.callback_query(F.data.startswith("expeditprice_"))
async def edit_price_start(callback: types.CallbackQuery, state: FSMContext):
    row_idx = int(callback.data.split("_")[1])
    await state.update_data(edit_row=row_idx)
    await state.set_state(EditExpState.waiting_for_new_price)
    await callback.message.delete()
    await callback.message.answer("Введите новую цену:", reply_markup=kb_reply.get_cancel_kb())
    await callback.answer()

@router.message(EditExpState.waiting_for_new_name)
async def edit_name_process(message: types.Message, state: FSMContext):
    data = await state.get_data()
    db.update_cell(data['edit_row'], "name", message.text, message.from_user.id)
    await message.answer("✅ Название обновлено!", reply_markup=kb_reply.get_main_menu())
    await state.clear()

@router.message(EditExpState.waiting_for_new_price)
async def edit_price_process(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число!")
    data = await state.get_data()
    db.update_cell(data['edit_row'], "price", int(message.text), message.from_user.id)
    await message.answer("✅ Цена обновлена!", reply_markup=kb_reply.get_main_menu())
    await state.clear()

@router.callback_query(F.data == "delcancel")
async def cancel_manage_inline(callback: types.CallbackQuery):
    await callback.message.edit_text("Действие отменено.")