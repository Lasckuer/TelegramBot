from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from redis.asyncio import Redis

class MaintenanceMiddleware(BaseMiddleware):
    def __init__(self, admin_id: int):
        self.admin_id = int(admin_id)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        redis: Redis = data.get("redis")
        is_maintenance = await redis.get("maintenance_mode")

        if is_maintenance == b"1":
            user = data.get("event_from_user")
            
            if user and user.id == self.admin_id:
                return await handler(event, data)
            
            if isinstance(event, Message):
                await event.answer(
                    "🛠 <b>Технические работы</b>\n\n"
                    "Бот сейчас обновляется. Пожалуйста, подождите пару минут!",
                    parse_mode="HTML"
                )
            elif isinstance(event, CallbackQuery):
                await event.answer("🛠 Идут технические работы...", show_alert=True)
            
            return

        return await handler(event, data)