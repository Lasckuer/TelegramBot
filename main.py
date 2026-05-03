import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import BOT_TOKEN
from app.handlers import get_handlers_router
from app.jobs import send_weekly_report, check_daily_subscriptions
from app.handlers.utils import db
from aiogram.client.session.aiohttp import AiohttpSession

logger = logging.getLogger(__name__)

log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler = RotatingFileHandler('bot_log.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
file_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])

async def main():
    proxy_url = os.getenv("PROXY_URL")
    session = AiohttpSession(proxy=proxy_url)
    
    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher()
    
    
    dp.include_router(get_handlers_router())
    
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_weekly_report, "cron", day_of_week="sun", hour=12, minute=0, args=[bot, db])
    scheduler.add_job(check_daily_subscriptions, "cron", hour=10, minute=0, args=[bot])
    scheduler.start()
    
    logger.info("\n" + "="*30 + "\n✅ БОТ ЗАПУЩЕН\n" + "="*30 + "\n")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот выключен")