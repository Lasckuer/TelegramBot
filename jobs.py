import os
import json
from datetime import datetime
from config import USER_ID

SUBS_FILE = "subs.json"

def load_subs():
    if not os.path.exists(SUBS_FILE):
        return []
    with open(SUBS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

async def send_weekly_report(bot, db):
    msg = db.get_monthly_analytics()
    await bot.send_message(USER_ID, f"📅 <b>Еженедельный отчет по расходам:</b>\n\n{msg}", parse_mode="HTML")

async def check_daily_subscriptions(bot):
    subs = load_subs()
    today_day = datetime.now().day
    
    for sub in subs:
        if sub['day'] == today_day:
            text = f"🔔 <b>Напоминание об оплате!</b>\nСегодня нужно оплатить: <b>{sub['name']}</b>\nСумма: {sub['amount']}р."
            await bot.send_message(USER_ID, text, parse_mode="HTML")