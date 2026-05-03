import asyncio
import logging
import os
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.handlers import get_handlers_router
from app.jobs import send_weekly_report, check_daily_subscriptions, check_daily_debts
from app.handlers.utils import db
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from logger import setup_logging 
from app.events import on_startup, on_shutdown
from app.middleware.maintenance import MaintenanceMiddleware

logger = logging.getLogger(__name__)
ADMIN_ID = int(os.getenv("ADMIN_ID"))
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    setup_logging()
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis = Redis.from_url(redis_url)
    
    storage = RedisStorage(redis=redis)
    
    proxy_url = os.getenv("PROXY_URL")
    session = AiohttpSession(proxy=proxy_url) if proxy_url else None
    
    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher(storage=storage)
    
    dp["redis"] = redis 
    maintenance_middleware = MaintenanceMiddleware(admin_id=ADMIN_ID)
    dp.message.middleware(maintenance_middleware)
    dp.callback_query.middleware(maintenance_middleware)
    
    dp.include_router(get_handlers_router())
    
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_weekly_report, "cron", day_of_week="sun", hour=12, minute=0, args=[bot, db])
    scheduler.add_job(check_daily_subscriptions, "cron", hour=10, minute=0, args=[bot])
    scheduler.add_job(check_daily_debts, "cron", hour=10, minute=5, args=[bot])
    scheduler.start()
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    logger.info("\n" + "="*30 + "\n✅ БОТ ЗАПУЩЕН\n" + "="*30 + "\n")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот выключен")