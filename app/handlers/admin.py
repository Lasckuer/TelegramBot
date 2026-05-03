import os
import time
import psutil
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from redis.asyncio import Redis

from app.handlers.utils import db 
from app.keyboards.inline.menus import get_admin_panel_kb, get_cancel_broadcast_kb

admin_router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PROCESS_START_TIME = time.time()

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()

@admin_router.callback_query(F.data == "open_admin_panel", F.from_user.id == ADMIN_ID)
async def open_admin_panel(callback: CallbackQuery):
    await callback.message.edit_text(
        "👑 <b>Панель администратора:</b>", 
        reply_markup=get_admin_panel_kb(), 
        parse_mode="HTML"
    )

@admin_router.callback_query(F.data == "admin_tech_toggle", F.from_user.id == ADMIN_ID)
async def toggle_tech_mode(callback: CallbackQuery, redis: Redis):
    current_status = await redis.get("maintenance_mode")
    if current_status == b"1":
        await redis.delete("maintenance_mode")
        await callback.answer("🟢 Режим тех. работ ВЫКЛЮЧЕН", show_alert=True)
    else:
        await redis.set("maintenance_mode", "1")
        await callback.answer("🔴 Режим тех. работ ВКЛЮЧЕН", show_alert=True)

@admin_router.callback_query(F.data == "admin_logs", F.from_user.id == ADMIN_ID)
async def show_logs_tail(callback: CallbackQuery):
    log_file = "bot_log.log"
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            tail = "".join(lines[-15:])
        
        if not tail.strip():
            tail = "Файл логов пока пуст."
            
        await callback.message.answer(f"<b>Последние логи:</b>\n<code>{tail}</code>", parse_mode="HTML")
    except FileNotFoundError:
        await callback.answer("Файл логов не найден!", show_alert=True)
    await callback.answer()

@admin_router.callback_query(F.data == "admin_stats", F.from_user.id == ADMIN_ID)
async def show_system_stats(callback: CallbackQuery):
    uptime_seconds = int(time.time() - PROCESS_START_TIME)
    uptime_str = f"{uptime_seconds // 3600}ч {(uptime_seconds % 3600) // 60}м"
    ram = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1)
    
    users_count = db.get_total_users_count()
    records_count = db.get_total_records_count()

    text = (
        "📊 <b>Статус системы</b>\n\n"
        f"⏱ <b>Uptime:</b> <code>{uptime_str}</code>\n"
        f"🖥 <b>CPU:</b> <code>{cpu}%</code>\n"
        f"💾 <b>RAM:</b> <code>{ram.percent}%</code> (Занято: {ram.used // 1048576} MB)\n\n"
        f"👥 <b>Пользователей:</b> <code>{users_count}</code>\n"
        f"📝 <b>Записей в БД:</b> <code>{records_count}</code>"
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@admin_router.callback_query(F.data == "admin_broadcast", F.from_user.id == ADMIN_ID)
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📢 <b>Режим рассылки</b>\n\n"
        "Отправь сообщение, которое нужно разослать всем пользователям (можно прикрепить фото, видео или файл).", 
        reply_markup=get_cancel_broadcast_kb(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_broadcast)

@admin_router.callback_query(F.data == "admin_cancel_broadcast", AdminStates.waiting_for_broadcast, F.from_user.id == ADMIN_ID)
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "👑 <b>Панель администратора:</b>", 
        reply_markup=get_admin_panel_kb(), 
        parse_mode="HTML"
    )

@admin_router.message(AdminStates.waiting_for_broadcast, F.from_user.id == ADMIN_ID)
async def execute_broadcast(message: Message, state: FSMContext, bot: Bot):
    users = db.get_all_users_ids()
    
    if not users:
        await state.clear()
        return await message.answer(
            "❌ <b>Ошибка:</b> В базе данных не найдено ни одного пользователя!\n"
            "Убедись, что метод get_all_users_ids() работает корректно.",
            parse_mode="HTML"
        )

    status_msg = await message.answer(f"⏳ Начинаю рассылку для {len(users)} пользователей...")
    
    success, failed = 0, 0
    for user_id in users:
        try:
            await bot.copy_message(
                chat_id=user_id, 
                from_chat_id=message.chat.id, 
                message_id=message.message_id
            )
            success += 1
        except Exception:
            failed += 1
        
        await asyncio.sleep(0.05)
        
    await state.clear()
    
    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"Успешно отправлено: <code>{success}</code>\n"
        f"Ошибок (бот заблокирован): <code>{failed}</code>", 
        parse_mode="HTML"
    )