from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import keyboards.reply as kb_reply
import keyboards.inline as kb_inline

router = Router()

@router.message(Command("start"))
@router.message(F.text == "Назад")
async def main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=kb_reply.get_main_menu())

@router.message(F.text == "💸 Расходы")
async def expenses_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("<b>Управление расходами:</b>", reply_markup=kb_inline.get_inline_expenses_menu(), parse_mode="HTML")

@router.message(F.text == "💰 Доходы")
async def incomes_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("<b>Управление доходами:</b>", reply_markup=kb_inline.get_inline_incomes_menu(), parse_mode="HTML")

@router.message(F.text == "📊 Аналитика")
async def analytics_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("<b>Финансовая сводка:</b>", reply_markup=kb_inline.get_inline_analytics_menu(), parse_mode="HTML")

@router.message(F.text == "⚙️ Настройки")
async def settings_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("<b>Настройки профиля:</b>", reply_markup=kb_inline.get_inline_settings_menu(), parse_mode="HTML")