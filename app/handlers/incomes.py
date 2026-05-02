import app.keyboards.inline as kb_inline
import app.keyboards.reply as kb_reply
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from app.states import IncomeForm
from app.database.db_manager import DatabaseManager
from app.handlers.common import main_menu

router = Router()
db = DatabaseManager()

LIMIT = 50000
SUBS_FILE = "subs.json"
CAT_MAP_FILE = "cat_map.json"
DEBTS_FILE = "debts.json"

# ==========================================
# --- ДОХОДЫ ---
# ==========================================
@router.message(IncomeForm.confirm)
async def process_income_confirm(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    
    db.add_income(
        user_id=user_id,
        source=data['source'],
        name=data['name'],
        amount=data['amount']
    )
    await message.answer("✅ Доход успешно записан!")
    await state.clear()
    
@router.callback_query(F.data == "menu_add_inc")
async def start_income(callback: types.CallbackQuery):
    await callback.message.edit_text("Выбери источник дохода:", reply_markup=kb_inline.get_inline_income_categories_kb("addinc"))
    await callback.answer()

@router.callback_query(F.data.startswith("addinc_"))
async def select_income_source(callback: types.CallbackQuery, state: FSMContext):
    source = callback.data.split("_")[1]
    await state.set_state(IncomeForm.source)
    await state.update_data(source=source)
    await state.set_state(IncomeForm.name)
    await callback.message.delete()
    await callback.message.answer(f"Источник: <b>{source}</b>.\nОт кого или за что этот доход?", parse_mode="HTML", reply_markup=kb_reply.get_cancel_kb())
    await callback.answer()

@router.message(IncomeForm.name)
async def process_income_name(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)
    await state.update_data(name=message.text)
    await state.set_state(IncomeForm.amount)
    await message.answer("Введите сумму дохода:")

@router.message(IncomeForm.amount)
async def process_income_amount(message: types.Message, state: FSMContext):
    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("Введите только число!")
    
    data = await state.get_data()
    user_id = message.from_user.id
    db.add_income(user_id, data['source'], data['name'], int(float(message.text)))
    
    await message.answer("✅ Доход успешно записан!", reply_markup=kb_reply.get_main_menu())
    await state.clear()

@router.callback_query(F.data == "menu_manage_inc")
async def manage_inc_stub(callback: types.CallbackQuery):
    await callback.answer("Управление доходами скоро появится ⏳", show_alert=True)
