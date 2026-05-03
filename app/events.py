import os
import logging
from aiogram import Bot

logger = logging.getLogger(__name__)

async def on_startup(bot: Bot):
    admin_id = os.getenv("ADMIN_ID")
    if not admin_id:
        return
        
    try:
        await bot.send_message(int(admin_id), "✅ Бот успешно обновлен и запущен!")
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение админу: {e}")

async def on_shutdown(bot: Bot):
    admin_id = os.getenv("ADMIN_ID")
    if not admin_id:
        return
        
    try:
        await bot.send_message(int(admin_id), "🔄 Бот ушел на перезагрузку/обновление...")
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение админу: {e}")