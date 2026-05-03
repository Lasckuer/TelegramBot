import os
import pandas as pd
from datetime import datetime
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
import app.keyboards.reply as kb_reply
import app.keyboards.inline as kb_inline
from app.states import ExportState
from app.database.db_manager import DatabaseManager

router = Router()
db = DatabaseManager()

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