import pandas as pd
from aiogram import Router, F, types
import app.keyboards.inline as kb_inline
from app.handlers.utils import db
from app.handlers.crypto import get_live_rates
from datetime import datetime, timedelta

router = Router()

@router.callback_query(F.data == "menu_ai_tips")
async def get_ai_assistant_tips(callback: types.CallbackQuery):
    msg = await callback.message.edit_text("🤖 Анализирую ваши данные...")
    
    user_id = callback.from_user.id
    df = db.get_all_df(user_id)
    
    if df.empty or len(df) < 5:
        return await msg.edit_text("🤖 Мне нужно больше данных для анализа (хотя бы за пару недель).")

    df['date_dt'] = pd.to_datetime(df['date'].str[:10], format="%d.%m.%Y", errors='coerce')
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    rates = await get_live_rates()
    df['price_rub'] = df.apply(lambda x: x['price'] * rates.get(x.get('currency', 'RUB'), 1.0), axis=1)

    now = datetime.now()
    day_of_month = now.day
    days_in_month = (now.replace(month=now.month % 12 + 1, day=1) - timedelta(days=1)).day

    curr_month_df = df[df['date_dt'].dt.month == now.month]
    prev_months_df = df[df['date_dt'].dt.month != now.month]
    
    tips = "🤖 <b>Советы AI-ассистента:</b>\n\n"
    found_insights = False

    if not prev_months_df.empty:
        avg_monthly = prev_months_df.groupby([prev_months_df['date_dt'].dt.month, 'category'])['price_rub'].sum().groupby('category').mean()
        curr_monthly = curr_month_df.groupby('category')['price_rub'].sum()

        for cat, curr_val in curr_monthly.items():
            avg_val = avg_monthly.get(cat, 0)
            if avg_val > 0:
                increase = (curr_val - avg_val) / avg_val
                if increase > 0.3:
                    tips += f"⚠️ <b>Аномалия:</b> В этом месяце траты на «{cat}» уже на {increase*100:.0f}% выше нормы.\n"
                    found_insights = True

    limit = db.get_user_limit(user_id)
    total_spent_now = curr_month_df['price_rub'].sum()
    
    if total_spent_now > 0:
        daily_avg = total_spent_now / day_of_month
        forecast_end_month = daily_avg * days_in_month
        
        if forecast_end_month > limit:
            overlimit_day = int(limit / daily_avg)
            tips += f"📉 <b>Прогноз:</b> При текущем темпе лимит в {limit}р закончится примерно через {overlimit_day - day_of_month} дней (к {overlimit_day} числу).\n"
            found_insights = True
        else:
            tips += f"✅ <b>Прогноз:</b> Вы идете в рамках лимита. К концу месяца останется ~{int(limit - forecast_end_month)}р.\n"

    if not found_insights:
        tips += "Траты выглядят стабильно. Продолжайте в том же духе!"

    await msg.edit_text(tips, parse_mode="HTML", reply_markup=kb_inline.get_inline_analytics_menu())