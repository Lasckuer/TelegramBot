import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from aiogram import Router, F, types
from aiogram.types import FSInputFile
import app.keyboards.inline as kb_inline
import app.keyboards.reply as kb_reply
from app.handlers.utils import db
from app.handlers.crypto import get_live_rates
from datetime import datetime


router = Router()
sns.set_theme(style="whitegrid", palette="pastel")


# ==========================================
# --- АНАЛИТИКА ---
# ==========================================
@router.callback_query(F.data == "show_graph")
async def send_graph(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    df = db.get_all_df(user_id) 
    
    if df.empty:
        await callback.answer("У вас пока нет данных для графика", show_alert=True)
        return

    df = df.rename(columns={'price': 'Стоимость', 'category': 'Категория'})

@router.callback_query(F.data == "menu_chart")
async def send_graph(callback: types.CallbackQuery):
    await callback.message.delete()
    msg = await callback.message.answer("Создаю график...")
    df = db.get_all_df(callback.from_user.id)
    if df.empty:
        await msg.delete()
        return await callback.message.answer("Нет данных для графика", reply_markup=kb_reply.get_main_menu())
    
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    summary = df.groupby('category')['price'].sum()
    
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
    
    user_id = callback.from_user.id
    df = db.get_all_df(user_id)
    if df.empty or 'date' not in df.columns:
        await callback.answer("Нет данных для сравнения.", show_alert=True)
        return

    df['date_dt'] = pd.to_datetime(df['date'], format="%d.%m.%Y", errors='coerce')
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)

    now = datetime.now()
    curr_month, curr_year = now.month, now.year
    
    if curr_month == 1:
        prev_month, prev_year = 12, curr_year - 1
    else:
        prev_month, prev_year = curr_month - 1, curr_year

    curr_df = df[(df['date_dt'].dt.month == curr_month) & (df['date_dt'].dt.year == curr_year)]
    prev_df = df[(df['date_dt'].dt.month == prev_month) & (df['date_dt'].dt.year == prev_year)]

    curr_grouped = curr_df.groupby('category')['price'].sum()
    prev_grouped = prev_df.groupby('category')['price'].sum()

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
    
@router.callback_query(F.data == "menu_trend")
async def send_trend_graph(callback: types.CallbackQuery):
    await callback.message.delete()
    msg = await callback.message.answer("📊 Рисую тренд расходов...")
    
    df = db.get_all_df(callback.from_user.id)
    if df.empty:
        return await msg.edit_text("Нет данных для графика.")

    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    # Парсим дату (предполагаем, что там день.месяц.год)
    df['date_dt'] = pd.to_datetime(df['date'].str[:10], format="%d.%m.%Y", errors='coerce')
    
    df['month'] = df['date_dt'].dt.to_period('M').astype(str)
    trend_data = df.groupby('month')['price'].sum().reset_index()

    plt.figure(figsize=(10, 5))
    sns.lineplot(data=trend_data, x='month', y='price', marker="o", linewidth=2.5, color="#4C72B0")
    plt.fill_between(trend_data['month'], trend_data['price'], alpha=0.2, color="#4C72B0")
    
    plt.title("Динамика расходов по месяцам", fontsize=16)
    plt.ylabel("Сумма (₽)")
    plt.xlabel("")
    plt.xticks(rotation=45)
    plt.tight_layout()

    graph_path = f"trend_{callback.from_user.id}.png"
    plt.savefig(graph_path, dpi=300)
    plt.close()

    await msg.delete()
    await callback.message.answer_photo(FSInputFile(graph_path), caption="📈 Твой тренд расходов")
    os.remove(graph_path)
    await callback.answer()
    
    
@router.callback_query(F.data == "menu_portfolio")
async def show_portfolio(callback: types.CallbackQuery):
    await callback.message.edit_text("⏳ Загружаю актуальные курсы валют...")
    
    rates = await get_live_rates()
    
    df = db.get_all_df(callback.from_user.id, table="incomes")
    
    total_rub = 0
    text = "💼 <b>Твой мультивалютный портфель:</b>\n\n"
    
    if df.empty or 'currency' not in df.columns:
        return await callback.message.edit_text("Ваш портфель пока пуст.")
        
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    balances = df.groupby('currency')['price'].sum()
    
    for currency, amount in balances.items():
        if amount <= 0:
            continue
            
        rate = rates.get(currency, 1.0)
        rub_value = amount * rate
        total_rub += rub_value
        
        if currency == 'RUB':
            text += f"🇷🇺 Рубли: <b>{amount:,.0f} ₽</b>\n"
        elif currency == 'USD':
            text += f"💵 Доллары: {amount:,.2f} $\n   <i>(~ {rub_value:,.0f} ₽ по курсу {rate:.2f})</i>\n"
        elif currency == 'EUR':
            text += f"💶 Евро: {amount:,.2f} €\n   <i>(~ {rub_value:,.0f} ₽ по курсу {rate:.2f})</i>\n"
        elif currency == 'BTC':
            text += f"₿ Bitcoin: {amount:.6f} BTC\n   <i>(~ {rub_value:,.0f} ₽ по курсу {rate:,.0f})</i>\n"
        elif currency == 'USDT':
            text += f"🪙 USDT: {amount:,.2f}\n   <i>(~ {rub_value:,.0f} ₽ по курсу {rate:.2f})</i>\n"
        else:
            text += f"💱 {currency}: {amount:,.2f}\n   <i>(~ {rub_value:,.0f} ₽)</i>\n"
            
    text += f"\n📊 <b>Общий капитал в рублях: {total_rub:,.0f} ₽</b>"
    
    from app.keyboards.inline import get_inline_analytics_menu
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_inline_analytics_menu())
    


@router.callback_query(F.data == "menu_balance")
async def show_balance(callback: types.CallbackQuery):
    msg = await callback.message.edit_text("⏳ Считаю баланс с учетом актуальных курсов валют...")
    
    rates = await get_live_rates()
    user_id = callback.from_user.id
    now = datetime.now()
    month_str = now.strftime("%m.%Y")
    
    total_exp_rub = 0
    total_inc_rub = 0
    exp_details = []
    inc_details = []
    
    df_exp = db.get_all_df(user_id, table="expenses")
    if not df_exp.empty and 'currency' in df_exp.columns:
        df_exp = df_exp[df_exp['date'].str.contains(month_str, na=False)]
        df_exp['price'] = pd.to_numeric(df_exp['price'], errors='coerce').fillna(0)
        for curr, amount in df_exp.groupby('currency')['price'].sum().items():
            if amount > 0:
                total_exp_rub += amount * rates.get(curr, 1.0)
                formatted_amt = f"{amount:,.0f}" if amount.is_integer() else f"{amount:,.2f}"
                exp_details.append(f"{formatted_amt} {curr}")
                
    df_inc = db.get_all_df(user_id, table="incomes")
    if not df_inc.empty and 'currency' in df_inc.columns:
        df_inc = df_inc[df_inc['date'].str.contains(month_str, na=False)]
        df_inc['price'] = pd.to_numeric(df_inc['price'], errors='coerce').fillna(0)
        for curr, amount in df_inc.groupby('currency')['price'].sum().items():
            if amount > 0:
                total_inc_rub += amount * rates.get(curr, 1.0)
                formatted_amt = f"{amount:,.0f}" if amount.is_integer() else f"{amount:,.2f}"
                inc_details.append(f"{formatted_amt} {curr}")
                
    balance = total_inc_rub - total_exp_rub
    limit = db.get_user_limit(user_id)
    
    inc_str = f"\n   <i>(состоит из: {', '.join(inc_details)})</i>" if inc_details else ""
    exp_str = f"\n   <i>(состоит из: {', '.join(exp_details)})</i>" if exp_details else ""
    
    text = f"📊 <b>Итог за {now.strftime('%B')}:</b>\n\n"
    text += f"🟢 Доходы: <b>{total_inc_rub:,.0f} ₽</b>{inc_str}\n"
    text += f"🔴 Расходы: <b>{total_exp_rub:,.0f} ₽</b>{exp_str}\n"
    text += f"🎯 Лимит: {limit:,.0f} ₽\n"
    text += f"➖➖➖➖➖➖➖➖\n"
    text += f"💰 Баланс: <b>{balance:,.0f} ₽</b>\n"
    
    await msg.edit_text(text, parse_mode="HTML", reply_markup=kb_inline.get_inline_analytics_menu())