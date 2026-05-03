import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from aiogram import Router, F, types
from aiogram.types import FSInputFile
import app.keyboards.reply as kb_reply
from app.handlers.utils import db

router = Router()
sns.set_theme(style="whitegrid", palette="pastel")

@router.callback_query(F.data == "show_graph")
async def send_graph_stub(callback: types.CallbackQuery):
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

@router.callback_query(F.data == "menu_trend")
async def send_trend_graph(callback: types.CallbackQuery):
    await callback.message.delete()
    msg = await callback.message.answer("📊 Рисую тренд расходов...")
    
    df = db.get_all_df(callback.from_user.id)
    if df.empty:
        return await msg.edit_text("Нет данных для графика.")

    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
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
    if os.path.exists(graph_path):
        os.remove(graph_path)
    await callback.answer()