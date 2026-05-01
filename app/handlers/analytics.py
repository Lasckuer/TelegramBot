import os
import pandas as pd
import matplotlib.pyplot as plt
from aiogram import Router, F, types
from aiogram.types import FSInputFile
import app.keyboards.inline as kb_inline
import app.keyboards.reply as kb_reply
from .utils import db

router = Router()


# ==========================================
# --- АНАЛИТИКА ---
# ==========================================
@router.callback_query(F.data == "menu_balance")
async def show_balance(callback: types.CallbackQuery):
    report = db.get_balance_report()
    await callback.message.edit_text(report, parse_mode="HTML", reply_markup=kb_reply.get_inline_analytics_menu())
    await callback.answer()

@router.callback_query(F.data == "menu_chart")
async def send_graph(callback: types.CallbackQuery):
    await callback.message.delete()
    msg = await callback.message.answer("Создаю график...")
    df = db.get_all_df()
    if df.empty:
        await msg.delete()
        return await callback.message.answer("Нет данных для графика", reply_markup=kb_reply.get_main_menu())
    
    df['Стоимость'] = pd.to_numeric(df['Стоимость'], errors='coerce').fillna(0)
    summary = df.groupby('Категория')['Стоимость'].sum()
    
    plt.figure(figsize=(10, 6))
    summary.plot(kind='pie', autopct='%1.1f%%', startangle=140)
    plt.title("Расходы по категориям")
    plt.ylabel("")
    
    graph_path = "graph.png"
    plt.savefig(graph_path)
    plt.close()
    
    await msg.delete()
    await callback.message.answer_photo(FSInputFile(graph_path), caption="Аналитика в графиках", reply_markup=kb_reply.get_main_menu())
    if os.path.exists(graph_path):
        os.remove(graph_path)
    await callback.answer()

@router.callback_query(F.data == "menu_compare")
async def compare_months(callback: types.CallbackQuery):
    from datetime import datetime
    
    df = db.get_all_df()
    if df.empty or 'Дата' not in df.columns:
        await callback.answer("Нет данных для сравнения.", show_alert=True)
        return

    df['Дата_dt'] = pd.to_datetime(df['Дата'], format="%d.%m.%Y", errors='coerce')
    df['Стоимость'] = pd.to_numeric(df['Стоимость'], errors='coerce').fillna(0)

    now = datetime.now()
    curr_month, curr_year = now.month, now.year
    
    if curr_month == 1:
        prev_month, prev_year = 12, curr_year - 1
    else:
        prev_month, prev_year = curr_month - 1, curr_year

    curr_df = df[(df['Дата_dt'].dt.month == curr_month) & (df['Дата_dt'].dt.year == curr_year)]
    prev_df = df[(df['Дата_dt'].dt.month == prev_month) & (df['Дата_dt'].dt.year == prev_year)]

    curr_grouped = curr_df.groupby('Категория')['Стоимость'].sum()
    prev_grouped = prev_df.groupby('Категория')['Стоимость'].sum()

    all_categories = set(curr_grouped.index).union(set(prev_grouped.index))

    if not all_categories:
        await callback.answer("Нет трат за периоды.", show_alert=True)
        return

    text = "📊 <b>Сравнение с прошлым месяцем:</b>\n\n"
    total_curr = curr_grouped.sum()
    total_prev = prev_grouped.sum()

    for cat in all_categories:
        curr_val = curr_grouped.get(cat, 0)
        prev_val = prev_grouped.get(cat, 0)

        if prev_val == 0 and curr_val > 0:
            text += f"🔹 <b>{cat}</b>: {curr_val}р (В прошлом месяце трат не было)\n"
        elif curr_val == 0 and prev_val > 0:
            text += f"🔹 <b>{cat}</b>: 0р (Траты упали на 100%, было {prev_val}р)\n"
        else:
            diff = curr_val - prev_val
            percent = abs(diff) / prev_val * 100
            if diff > 0:
                text += f"🔺 <b>{cat}</b>: {curr_val}р (На {percent:.1f}% больше)\n"
            elif diff < 0:
                text += f"🔻 <b>{cat}</b>: {curr_val}р (На {percent:.1f}% меньше)\n"
            else:
                text += f"➖ <b>{cat}</b>: {curr_val}р (Без изменений)\n"

    text += "\n💰 <b>ИТОГО:</b>\n"
    if total_prev == 0:
        text += f"В этом месяце: {total_curr}р (В прошлом не было трат)"
    else:
        diff_total = total_curr - total_prev
        perc_total = abs(diff_total) / total_prev * 100
        if diff_total > 0:
            text += f"🔺 Вы потратили на <b>{perc_total:.1f}% больше</b> ({total_curr}р против {total_prev}р)"
        elif diff_total < 0:
            text += f"🔻 Вы <b>сэкономили {perc_total:.1f}%</b> ({total_curr}р против {total_prev}р)"
        else:
            text += f"➖ Потрачено ровно столько же ({total_curr}р)"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb_inline.get_inline_analytics_menu())
    await callback.answer()