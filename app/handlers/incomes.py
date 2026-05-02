import app.keyboards.inline as kb_inline
import app.keyboards.reply as kb_reply
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from app.states import IncomeForm, EditIncState
from app.database.db_manager import DatabaseManager
from app.handlers.common import main_menu

router = Router()
db = DatabaseManager()

@router.callback_query(F.data == "menu_add_inc")
async def start_income(callback: types.CallbackQuery):
    await callback.message.edit_text("Выбери категорию дохода:", reply_markup=kb_inline.get_inline_income_categories_kb("addinc"))
    await callback.answer()

@router.callback_query(F.data.startswith("addinc_"))
async def select_income_category(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[1]
    await state.update_data(category=category)
    await state.set_state(IncomeForm.name)
    await callback.message.delete()
    await callback.message.answer(f"Категория: <b>{category}</b>.\nВведите источник дохода:", parse_mode="HTML", reply_markup=kb_reply.get_cancel_kb())
    await callback.answer()

@router.message(IncomeForm.name)
async def process_income_name(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)
    await state.update_data(name=message.text)
    await state.set_state(IncomeForm.price)
    await message.answer("Введите сумму:")

@router.message(IncomeForm.price)
async def process_income_price(message: types.Message, state: FSMContext):
    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("Введите число!")
    data = await state.get_data()
    db.add_income(message.from_user.id, data['category'], data['name'], int(float(message.text)))
    await message.answer("✅ Доход записан!", reply_markup=kb_reply.get_main_menu())
    await state.clear()

@router.callback_query(F.data == "menu_manage_inc")
async def start_manage_incomes(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите категорию дохода:", reply_markup=kb_inline.get_inline_income_categories_kb("mnginc"))
    await callback.answer()

@router.callback_query(F.data.startswith("mnginc_"))
async def show_income_items(callback: types.CallbackQuery):
    category = callback.data.split("_")[1]
    items = db.get_records_by_category(category, callback.from_user.id, table="incomes") 
    if not items:
        return await callback.message.edit_text(f"В категории «{category}» пока пусто.")
    await callback.message.edit_text(f"Последние доходы ({category}):", reply_markup=kb_inline.get_inline_manage_items_kb(items, prefix="incitem"))
    await callback.answer()

@router.callback_query(F.data.startswith("incitem_"))
async def income_item_actions(callback: types.CallbackQuery):
    row_idx = int(callback.data.split("_")[1])
    await callback.message.edit_text("Выберите действие:", reply_markup=kb_inline.get_inline_item_action_kb(row_idx, prefix="inc"))
    await callback.answer()

@router.callback_query(F.data.startswith("incdelconfirm_"))
async def execute_delete_income(callback: types.CallbackQuery):
    row_idx = int(callback.data.split("_")[1])
    db.delete_by_row(row_idx, callback.from_user.id, table="incomes") 
    await callback.message.edit_text("✅ Доход удален.")
    await callback.answer()

@router.callback_query(F.data.startswith("inceditname_"))
async def edit_income_name_start(callback: types.CallbackQuery, state: FSMContext):
    row_idx = int(callback.data.split("_")[1])
    await state.update_data(edit_row=row_idx)
    await state.set_state(EditIncState.waiting_for_new_name)
    await callback.message.delete()
    await callback.message.answer("📝 Введите новый источник (от кого):", reply_markup=kb_reply.get_cancel_kb())
    await callback.answer()

@router.callback_query(F.data.startswith("inceditprice_"))
async def edit_income_price_start(callback: types.CallbackQuery, state: FSMContext):
    row_idx = int(callback.data.split("_")[1])
    await state.update_data(edit_row=row_idx)
    await state.set_state(EditIncState.waiting_for_new_price)
    await callback.message.delete()
    await callback.message.answer("💰 Введите новую сумму:", reply_markup=kb_reply.get_cancel_kb())
    await callback.answer()

@router.message(EditIncState.waiting_for_new_name)
async def edit_income_name_process(message: types.Message, state: FSMContext):
    data = await state.get_data()
    db.update_cell(data['edit_row'], "name", message.text, message.from_user.id, table="incomes")
    await message.answer("✅ Источник обновлен!", reply_markup=kb_reply.get_main_menu())
    await state.clear()

@router.message(EditIncState.waiting_for_new_price)
async def edit_income_price_process(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число!")
    data = await state.get_data()
    db.update_cell(data['edit_row'], "price", int(message.text), message.from_user.id, table="incomes")
    await message.answer("✅ Сумма обновлена!", reply_markup=kb_reply.get_main_menu())
    await state.clear()