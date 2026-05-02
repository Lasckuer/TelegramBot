import os
import pandas as pd
from datetime import datetime
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

import app.keyboards.reply as kb_reply
import app.keyboards.inline as kb_inline
from app.states import LimitState, SubState, ExportState
from app.database.db_manager import DatabaseManager
from app.handlers.utils import load_subs, save_subs
from app.handlers.common import main_menu

router = Router()
db = DatabaseManager()

SUBS_FILE = "subs.json"
CAT_MAP_FILE = "cat_map.json"
DEBTS_FILE = "debts.json"

# ==========================================
# --- НАСТРОЙКИ ---
# ==========================================
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

@router.callback_query(F.data == "menu_export")
async def export_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите начальную дату для экспорта:", reply_markup=kb_inline.get_calendar_kb())
    await state.set_state(ExportState.start_date)
    await callback.answer()

@router.callback_query(F.data.startswith("calendar_nav_"))
async def calendar_nav(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    year, month = int(parts[2]), int(parts[3])
    await callback.message.edit_reply_markup(reply_markup=kb_inline.get_calendar_kb(year, month))
    await callback.answer()

@router.callback_query(F.data == "calendar_ignore")
async def calendar_ignore(callback: types.CallbackQuery):
    await callback.answer()

@router.callback_query(F.data == "calendar_cancel")
async def calendar_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Экспорт отменен.", reply_markup=kb_reply.get_main_menu())

@router.callback_query(F.data.startswith("calendar_day_"))
async def calendar_day(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    year, month, day = int(parts[2]), int(parts[3]), int(parts[4])
    selected_date = datetime(year, month, day)
    current_state = await state.get_state()

    if current_state == ExportState.start_date.state:
        await state.update_data(start_date=selected_date)
        await callback.message.edit_text(
            f"Начальная дата: {selected_date.strftime('%d.%m.%Y')}\nВыберите конечную дату:",
            reply_markup=kb_inline.get_calendar_kb(year, month)
        )
        await state.set_state(ExportState.end_date)
    
    elif current_state == ExportState.end_date.state:
        data = await state.get_data()
        start_date = data['start_date']
        end_date = selected_date
        if end_date < start_date:
            start_date, end_date = end_date, start_date

        await callback.message.delete()
        await callback.message.answer(f"Формирую отчет...", reply_markup=kb_reply.get_main_menu())
        await state.clear()

        df = db.get_all_df(callback.from_user.id)
        if df.empty or 'date' not in df.columns:
            return await callback.message.answer("Нет данных для экспорта.")

        df['date_dt'] = pd.to_datetime(df['date'], format="%d.%m.%Y", errors='coerce')
        filtered_df = df[(df['date_dt'] >= start_date) & (df['date_dt'] <= end_date)].copy()
        filtered_df.drop(columns=['date_dt'], inplace=True, errors='ignore')

        if filtered_df.empty:
            return await callback.message.answer("За этот период записей нет.")

        file_path = f"export_{callback.from_user.id}.xlsx"
        filtered_df.to_excel(file_path, index=False)
        await callback.message.answer_document(FSInputFile(file_path), caption="Excel отчет")
        if os.path.exists(file_path):
            os.remove(file_path)
