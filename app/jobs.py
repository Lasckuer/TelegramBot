import os
import json
import logging
from datetime import datetime
from app.database.db_manager import DatabaseManager
import app.keyboards.inline as kb_inline

logger = logging.getLogger(__name__)
db_internal = DatabaseManager()
SUBS_FILE = "subs.json"
DEBTS_FILE = "debts.json"

def load_subs():
    if not os.path.exists(SUBS_FILE): return []
    try:
        with open(SUBS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки подписок: {e}")
        return []

def load_debts():
    if not os.path.exists(DEBTS_FILE): return []
    try:
        with open(DEBTS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки долгов: {e}")
        return []

async def send_weekly_report(bot, db):
    df_all = db.get_all_df() 
    if df_all.empty: return
    user_ids = df_all['user_id'].unique()
    for uid in user_ids:
        try:
            report = db.get_balance_report(uid)
            await bot.send_message(uid, f"📅 <b>Ваш еженедельный финансовый отчет:</b>\n\n{report}", parse_mode="HTML")
            logger.info(f"Еженедельный отчет отправлен пользователю {uid}")
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
                logger.info(f"Уведомление о подписке {sub['name']} отправлено пользователю {sub['user_id']}")
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
                logger.info(f"Напоминание о долге от {debt['person']} отправлено пользователю {debt['user_id']}")
            except Exception as e:
                logger.error(f"Ошибка уведомления о долге для {debt.get('user_id')}: {e}")