import re
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
import app.keyboards.inline as kb_inline
import app.keyboards.reply as kb_reply
from app.states import ExpenseForm
from app.database.db_manager import DatabaseManager
from app.handlers.common.base import main_menu
from app.handlers.crypto import get_live_rates
from app.handlers.utils import load_cat_map, save_cat_map

router = Router()
db = DatabaseManager()

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
    await callback.message.answer(
        f"Внесение расхода в <b>{category}</b>.\nВведите название:", 
        parse_mode="HTML", 
        reply_markup=kb_reply.get_cancel_kb()
    )
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
    text = message.text.lower().strip()
    
    match = re.search(r'^([\d\.]+)', text)
    if not match:
        return await message.answer("Начните ввод с числа (например, 1500 или 20 usd).")
        
    try:
        amount = float(match.group(1))
    except ValueError:
        return await message.answer("Неверный формат числа.")
        
    currency = 'RUB'
    if 'usd' in text or '$' in text: currency = 'USD'
    elif 'eur' in text or '€' in text: currency = 'EUR'
    elif 'btc' in text: currency = 'BTC'
    elif 'usdt' in text: currency = 'USDT'
    
    rates = await get_live_rates()
    rate = rates.get(currency, 1.0)
    amount_in_rub = amount * rate
    
    user_id = message.from_user.id
    user_limit = db.get_user_limit(user_id)
    
    if amount_in_rub > user_limit:
        await message.answer(f"⚠️ Внимание! Трата (~{amount_in_rub:,.0f} ₽) превышает ваш месячный лимит {user_limit} ₽!")
    
    await state.update_data(price=amount, currency=currency)
    await state.set_state(ExpenseForm.shop)
    
    formatted_amount = int(amount) if amount.is_integer() else amount
    await message.answer(f"Сумма: {formatted_amount} {currency}.\nВ каком магазине? (или 'нет'):")

@router.message(ExpenseForm.shop)
async def process_shop(message: types.Message, state: FSMContext):
    data = await state.get_data()
    shop = message.text if message.text.lower() != 'нет' else "-"
    user_id = message.from_user.id
    
    db.add_expense(
        user_id=user_id, 
        category=data['category'], 
        name=data['name'], 
        price=data['price'], 
        shop=shop,
        currency=data.get('currency', 'RUB')
    )
    
    if shop != "-":
        cmap = load_cat_map()
        cmap[shop.lower().strip()] = data['category']
        save_cat_map(cmap)
        
    await message.answer("✅ Расход успешно записан!", reply_markup=kb_reply.get_main_menu())
    await state.clear()

@router.message(ExpenseForm.confirm)
async def process_confirm(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    
    db.add_expense(
        user_id=user_id, 
        category=data['category'], 
        name=data['name'], 
        price=data['price'], 
        shop=data.get('shop', '-')
    )
    await message.answer("✅ Запись сохранена!")
    await state.clear()