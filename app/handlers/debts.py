import time
from datetime import datetime
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
import app.keyboards.inline as kb_inline
import app.keyboards.reply as kb_reply
from app.states import DebtForm
from app.handlers.common import main_menu
from app.handlers.utils import load_debts, save_debts, load_subs, db

router = Router()

@router.message(F.text == "🤝 Долги")
async def debts_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("<b>Трекер долгов:</b>", reply_markup=kb_inline.get_inline_debts_menu(), parse_mode="HTML")

@router.callback_query(F.data.startswith("subpay_"))
async def process_sub_payment(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1])
    subs = load_subs()
    if idx < len(subs):
        sub = subs[idx]
        db.add_expense(user_id=callback.from_user.id, category="Ежемесячные", name=sub['name'], price=sub['amount'], shop="-")
        await callback.message.edit_text(f"✅ Оплата <b>{sub['name']}</b> ({sub['amount']}р) занесена в расходы.", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("subcancel_"))
async def cancel_sub_payment(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1])
    subs = load_subs()
    if idx < len(subs):
        await callback.message.edit_text(f"❌ Списание <b>{subs[idx]['name']}</b> пропущено.", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "menu_add_debt")
async def add_debt_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Кому вы дали в долг?", reply_markup=kb_reply.get_cancel_kb())
    await state.set_state(DebtForm.person)
    await callback.answer()

@router.message(DebtForm.person)
async def process_debt_person(message: types.Message, state: FSMContext):
    if message.text == "Назад": return await main_menu(message, state)
    await state.update_data(person=message.text)
    await state.set_state(DebtForm.amount)
    await message.answer("Какую сумму (число)?")

@router.message(DebtForm.amount)
async def process_debt_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("Только число!")
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

@router.callback_query(F.data == "menu_list_debts")
async def list_debts(callback: types.CallbackQuery):
    debts = load_debts()
    if not debts:
        return await callback.message.edit_text("🎉 У вас нет активных долгов!", reply_markup=kb_inline.get_inline_debts_menu())
    text = "<b>Активные долги:</b>\n\n"
    for d in debts:
        text += f"👤 <b>{d['person']}</b>: {d['amount']}р (До: {d['deadline']})\n"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb_inline.get_inline_debts_menu())
    for d in debts:
        await callback.message.answer(f"Отметить возврат от {d['person']} ({d['amount']}р)?", reply_markup=kb_inline.get_inline_debt_return_kb(d['id']))
    await callback.answer()

@router.callback_query(F.data.startswith("debtret_"))
async def process_debt_return(callback: types.CallbackQuery):
    debt_id = callback.data.split("_")[1]
    debts = load_debts()
    debt_to_return = next((d for d in debts if d['id'] == debt_id), None)
    if debt_to_return:
        db.add_income(user_id=callback.from_user.id, category="Переводы", name=f"Возврат долга ({debt_to_return['person']})", price=debt_to_return['amount'])
        debts = [d for d in debts if d['id'] != debt_id]
        save_debts(debts)
        await callback.message.edit_text(f"✅ Долг от <b>{debt_to_return['person']}</b> закрыт!\nСумма {debt_to_return['amount']}р добавлена в доходы.", parse_mode="HTML")
    else:
        await callback.message.edit_text("Этот долг уже закрыт.")
    await callback.answer()