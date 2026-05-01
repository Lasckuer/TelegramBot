import os
import json
from datetime import datetime
from config import USER_ID
import keyboards as kb

SUBS_FILE = "subs.json"
DEBTS_FILE = "debts.json"

def load_subs():
    if not os.path.exists(SUBS_FILE):
        return []
    with open(SUBS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_debts():
    if not os.path.exists(DEBTS_FILE):
        return []
    with open(DEBTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

async def send_weekly_report(bot, db):
    msg = db.get_monthly_analytics()
    await bot.send_message(USER_ID, f"📅 <b>Еженедельный отчет:</b>\n\n{msg}", parse_mode="HTML")

async def check_daily_subscriptions(bot):
    subs = load_subs()
    today_day = datetime.now().day
    for idx, sub in enumerate(subs):
        if sub['day'] == today_day:
            text = f"🔔 <b>Оплата подписки!</b>\nСегодня день списания за <b>{sub['name']}</b> ({sub['amount']}р).\nЗанести в расходы?"
            await bot.send_message(USER_ID, text, parse_mode="HTML", reply_markup=kb.get_inline_sub_action_kb(idx))

async def check_daily_debts(bot):
    debts = load_debts()
    today_str = datetime.now().strftime("%d.%m.%Y")
    for debt in debts:
        if debt['deadline'] == today_str:
            text = f"⚠️ <b>Напоминание о долге!</b>\nСегодня <b>{debt['person']}</b> должен вернуть {debt['amount']}р."
            await bot.send_message(USER_ID, text, parse_mode="HTML", reply_markup=kb.get_inline_debt_return_kb(debt['id']))