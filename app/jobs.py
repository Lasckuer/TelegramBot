import logging
from datetime import datetime
import app.keyboards.inline as kb_inline
from app.handlers.utils import load_subs, load_debts

logger = logging.getLogger(__name__)

async def send_weekly_report(bot, db):
    df_all = db.get_all_df() 
    if df_all.empty: 
        return
        
    user_ids = df_all['user_id'].unique()
    for uid in user_ids:
        try:
            report = db.get_balance_report(uid)
            await bot.send_message(uid, f"📅 <b>Ваш еженедельный финансовый отчет:</b>\n\n{report}", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка отправки еженедельного отчета пользователю {uid}: {e}")
            
async def check_daily_subscriptions(bot):
    subs = load_subs()
    today_day = datetime.now().day
    
    for idx, sub in enumerate(subs):
        if sub.get('day') == today_day:
            text = f"🔔 <b>Оплата подписки!</b>\nСегодня день списания за <b>{sub['name']}</b> ({sub['amount']}р).\nЗанести в расходы?"
            try:
                await bot.send_message(sub['user_id'], text, parse_mode="HTML", reply_markup=kb_inline.get_inline_sub_action_kb(idx))
            except Exception as e:
                logger.error(f"Ошибка уведомления по подписке для {sub.get('user_id')}: {e}")

async def check_daily_debts(bot):
    debts = load_debts()
    today_str = datetime.now().strftime("%d.%m.%Y")
    
    for debt in debts:
        if debt.get('deadline') == today_str:
            text = f"⚠️ <b>Напоминание о долге!</b>\nСегодня <b>{debt['person']}</b> должен вернуть {debt['amount']}р."
            try:
                await bot.send_message(debt['user_id'], text, parse_mode="HTML", reply_markup=kb_inline.get_inline_debt_return_kb(debt['id']))
            except Exception as e:
                logger.error(f"Ошибка уведомления о долге для {debt.get('user_id')}: {e}")