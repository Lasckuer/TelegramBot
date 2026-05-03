import pandas as pd
from aiogram import Router, F, types
from app.handlers.utils import db
from app.handlers.crypto import get_live_rates
from app.keyboards.inline import get_inline_analytics_menu

router = Router()

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
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_inline_analytics_menu())