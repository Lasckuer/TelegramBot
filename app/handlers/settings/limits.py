from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
import app.keyboards.reply as kb_reply
from app.states import LimitState
from app.database.db_manager import DatabaseManager

router = Router()
db = DatabaseManager()

@router.callback_query(F.data == "menu_limits")
async def show_limits(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    
    user_id = callback.from_user.id
    current_limit = db.get_user_limit(user_id)
    
    await callback.message.answer(
        f"Ваш текущий лимит: {current_limit}р.\nВведите новое число для изменения:", 
        reply_markup=kb_reply.get_cancel_kb()
    )
    await state.set_state(LimitState.waiting_for_limit)

@router.message(LimitState.waiting_for_limit)
async def set_limit(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        new_limit = int(message.text)
        user_id = message.from_user.id
        
        db.set_user_limit(user_id, new_limit)
        
        await message.answer(f"✅ Ваш персональный лимит изменен: {new_limit}р", reply_markup=kb_reply.get_main_menu())
        await state.clear()
    else:
        await message.answer("Введите число.")