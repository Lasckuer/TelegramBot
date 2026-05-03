from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
import app.keyboards.reply as kb_reply
from app.states import SubState
from app.handlers.utils import load_subs, save_subs
from app.handlers.common.base import main_menu

router = Router()

@router.callback_query(F.data == "menu_notifications")
async def setup_notifications(callback: types.CallbackQuery, state: FSMContext):
    subs = load_subs()
    text = "🗓 Ваши текущие подписки/платежи:\n"
    if not subs:
        text += "Пусто.\n"
    else:
        for s in subs:
            text += f"🔹 {s['name']} — {s['amount']}р (День оплаты: {s['day']}-го числа)\n"
    
    text += "\nЧтобы добавить новое уведомление, введите название подписки:"
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=kb_reply.get_cancel_kb())
    await state.set_state(SubState.waiting_for_name)
    await callback.answer()

@router.message(SubState.waiting_for_name)
async def sub_name_process(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)
    await state.update_data(name=message.text)
    await message.answer("Введите сумму платежа (число):")
    await state.set_state(SubState.waiting_for_amount)

@router.message(SubState.waiting_for_amount)
async def sub_amount_process(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Пожалуйста, введите только число.")
    await state.update_data(amount=int(message.text))
    await message.answer("В какой день месяца присылать уведомление? (число от 1 до 31):")
    await state.set_state(SubState.waiting_for_day)

@router.message(SubState.waiting_for_day)
async def sub_day_process(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (1 <= int(message.text) <= 31):
        return await message.answer("Введите корректный день (число от 1 до 31).")
    
    data = await state.get_data()
    new_sub = {"name": data['name'], "amount": data['amount'], "day": int(message.text)}
    subs = load_subs()
    subs.append(new_sub)
    save_subs(subs)
    
    await message.answer(f"✅ Напоминание сохранено!\n{new_sub['name']} ({new_sub['amount']}р) — {new_sub['day']}-го числа каждого месяца.", reply_markup=kb_reply.get_main_menu())
    await state.clear()