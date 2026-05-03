import time
from datetime import datetime
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
import app.keyboards.reply as kb_reply
from app.states import DebtForm
from app.handlers.common.base import main_menu
from app.handlers.utils import load_debts, save_debts

router = Router()

@router.callback_query(F.data == "menu_add_debt")
async def add_debt_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Кому вы дали в долг?", reply_markup=kb_reply.get_cancel_kb())
    await state.set_state(DebtForm.person)
    await callback.answer()

@router.message(DebtForm.person)
async def process_debt_person(message: types.Message, state: FSMContext):
    if message.text == "Назад": 
        return await main_menu(message, state)
    await state.update_data(person=message.text)
    await state.set_state(DebtForm.amount)
    await message.answer("Какую сумму (число)?")

@router.message(DebtForm.amount)
async def process_debt_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): 
        return await message.answer("Только число!")
    await state.update_data(amount=int(message.text))
    await state.set_state(DebtForm.deadline)
    await message.answer("До какого числа (формат ДД.ММ.ГГГГ)?")

@router.message(DebtForm.deadline)
async def process_debt_deadline(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%d.%m.%Y")
    except ValueError:
        return await message.answer("Неверный формат! Введите как 15.05.2026:")
    
    data = await state.get_data()
    debts = load_debts()
    debt_id = str(int(time.time()))
    
    debts.append({
        "id": debt_id,
        "user_id": message.from_user.id,
        "person": data['person'],
        "amount": data['amount'],
        "deadline": message.text
    })
    
    save_debts(debts)
    await message.answer(f"✅ Долг записан! Напомню {message.text}.", reply_markup=kb_reply.get_main_menu())
    await state.clear()