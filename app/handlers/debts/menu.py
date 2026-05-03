from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
import app.keyboards.inline as kb_inline

router = Router()

@router.message(F.text == "🤝 Долги")
async def debts_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("<b>Трекер долгов:</b>", reply_markup=kb_inline.get_inline_debts_menu(), parse_mode="HTML")