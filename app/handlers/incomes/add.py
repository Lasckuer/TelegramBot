import re
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
import app.keyboards.inline as kb_inline
import app.keyboards.reply as kb_reply
from app.states import IncomeForm
from app.database.db_manager import DatabaseManager
from app.handlers.common.base import main_menu

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
    text = message.text.lower().strip()
    
    match = re.search(r'^([\d\.]+)', text)
    if not match:
        return await message.answer("Пожалуйста, начните ввод с числа (например, 1000 или 150 usd).")
    
    try:
        price = float(match.group(1))
    except ValueError:
        return await message.answer("Неверный формат числа.")
    
    currency = 'RUB'
    if 'usd' in text or '$' in text:
        currency = 'USD'
    elif 'eur' in text or '€' in text:
        currency = 'EUR'
    elif 'btc' in text:
        currency = 'BTC'
    elif 'eth' in text:
        currency = 'ETH'
    elif 'usdt' in text:
        currency = 'USDT'
        
    data = await state.get_data()
    
    db.add_income(
        user_id=message.from_user.id, 
        category=data['category'], 
        name=data['name'], 
        price=price, 
        currency=currency
    )
    
    if price.is_integer():
        price = int(price)
        
    await message.answer(f"✅ Доход записан: {price} {currency}!", reply_markup=kb_reply.get_main_menu())
    await state.clear()