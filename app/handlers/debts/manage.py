from aiogram import Router, F, types
import app.keyboards.inline as kb_inline
from app.handlers.utils import load_debts, save_debts, db

router = Router()

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