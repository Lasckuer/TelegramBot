from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import app.keyboards.reply as kb_reply

router = Router()

@router.message(Command("start"))
@router.message(F.text == "Назад")
async def main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=kb_reply.get_main_menu())