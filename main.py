import asyncio
import logging
from logging.handlers import RotatingFileHandler
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from handlers import router, db
from jobs import send_weekly_report, check_daily_subscriptions
from config import BOT_TOKEN, USER_ID
from middlewares import SecurityMiddleware

log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = RotatingFileHandler('bot_log.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    dp.message.middleware(SecurityMiddleware(USER_ID))
    dp.callback_query.middleware(SecurityMiddleware(USER_ID))
    
    dp.include_router(router)
    
    # Настройка планировщика
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    # Передаем bot и db в функции планировщика
    scheduler.add_job(send_weekly_report, "cron", day_of_week="sun", hour=12, minute=0, args=[bot, db])
    scheduler.add_job(check_daily_subscriptions, "cron", hour=10, minute=0, args=[bot])
    scheduler.start()
    
    print("\n" + "="*30 + "\n✅ БОТ ЗАПУЩЕН\n" + "="*30 + "\n")
    await dp.start_polling(bot)
    
    

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Бот выключен")