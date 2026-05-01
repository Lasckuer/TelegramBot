import asyncio
import os
import json
import logging
import matplotlib.pyplot as plt
import pandas as pd
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None

from config import BOT_TOKEN, USER_ID, PROVERKA_CHEKA_TOKEN
from gsheets import GoogleTable

# Настройки
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
user_id = int(USER_ID)
dp = Dispatcher()
db = GoogleTable()

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

LIMIT = 50000 # Дефолтный лимит, чтобы код не падал, если он еще не задан
SUBS_FILE = "subs.json"

# --- РАБОТА С ПОДПИСКАМИ (ХРАНЕНИЕ В JSON) ---
def load_subs():
    if not os.path.exists(SUBS_FILE):
        return []
    with open(SUBS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_subs(subs):
    with open(SUBS_FILE, 'w', encoding='utf-8') as f:
        json.dump(subs, f, ensure_ascii=False, indent=4)

# --- СОСТОЯНИЯ ---
class ExpenseForm(StatesGroup):
    category = State()
    name = State()
    price = State()
    shop = State()

class DeleteState(StatesGroup):
    selecting_category = State()
    selecting_item = State()

class LimitState(StatesGroup):
    waiting_for_limit = State()

class SearchState(StatesGroup):
    waiting_for_query = State()

class SubState(StatesGroup):
    waiting_for_name = State()
    waiting_for_amount = State()
    waiting_for_day = State()

# --- КЛАВИАТУРЫ ---
def get_main_menu():
    buttons = [
        [KeyboardButton(text="Расходы"), KeyboardButton(text="Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_expenses_menu():
    buttons = [
        [KeyboardButton(text="Внести расход"), KeyboardButton(text="Удалить запись")],
        [KeyboardButton(text="Поиск"), KeyboardButton(text="Отчеты")],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_settings_menu():
    buttons = [
        [KeyboardButton(text="Экспорт"), KeyboardButton(text="График")],
        [KeyboardButton(text="Лимиты"), KeyboardButton(text="Уведомления")],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_categories_kb():
    buttons = [
        [KeyboardButton(text="Продукты"), KeyboardButton(text="Развлечения")],
        [KeyboardButton(text="Ежемесячные"), KeyboardButton(text="Остальное")],
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_cancel_kb():
    buttons = [[KeyboardButton(text="Назад")]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# --- НАВИГАЦИЯ ПО МЕНЮ ---
@dp.message(Command("start"))
@dp.message(F.text == "Назад")
async def main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=get_main_menu())

@dp.message(F.text == "Расходы")
async def expenses_menu(message: types.Message):
    await message.answer("Раздел 'Расходы':", reply_markup=get_expenses_menu())

@dp.message(F.text == "Настройки")
async def settings_menu(message: types.Message):
    await message.answer("Раздел 'Настройки':", reply_markup=get_settings_menu())


# --- УВЕДОМЛЕНИЯ О ПОДПИСКАХ ---
@dp.message(F.text == "Уведомления")
async def setup_notifications(message: types.Message, state: FSMContext):
    subs = load_subs()
    text = "🗓 Ваши текущие подписки/платежи:\n"
    if not subs:
        text += "Пусто.\n"
    else:
        for s in subs:
            text += f"🔹 {s['name']} — {s['amount']}р (День оплаты: {s['day']}-го числа)\n"
    
    text += "\nЧтобы добавить новое уведомление, введите название подписки (например, 'Spotify' или 'Интернет'):"
    await message.answer(text, reply_markup=get_cancel_kb())
    await state.set_state(SubState.waiting_for_name)

@dp.message(SubState.waiting_for_name)
async def sub_name_process(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)
    
    await state.update_data(name=message.text)
    await message.answer("Введите сумму платежа (число):")
    await state.set_state(SubState.waiting_for_amount)

@dp.message(SubState.waiting_for_amount)
async def sub_amount_process(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Пожалуйста, введите только число.")
    
    await state.update_data(amount=int(message.text))
    await message.answer("В какой день месяца присылать уведомление? (число от 1 до 31):")
    await state.set_state(SubState.waiting_for_day)

@dp.message(SubState.waiting_for_day)
async def sub_day_process(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (1 <= int(message.text) <= 31):
        return await message.answer("Введите корректный день (число от 1 до 31).")
    
    data = await state.get_data()
    new_sub = {
        "name": data['name'],
        "amount": data['amount'],
        "day": int(message.text)
    }
    
    subs = load_subs()
    subs.append(new_sub)
    save_subs(subs)
    
    await message.answer(f"✅ Напоминание сохранено!\n{new_sub['name']} ({new_sub['amount']}р) — {new_sub['day']}-го числа каждого месяца.", reply_markup=get_settings_menu())
    await state.clear()


# --- АВТОМАТИЗАЦИЯ (РАССЫЛКИ И НАПОМИНАНИЯ) ---
async def send_weekly_report():
    msg = db.get_monthly_analytics()
    # Отправляем сообщение пользователю
    await bot.send_message(user_id, f"📅 <b>Еженедельный отчет по расходам:</b>\n\n{msg}", parse_mode="HTML")

async def check_daily_subscriptions():
    subs = load_subs()
    today_day = datetime.now().day
    
    for sub in subs:
        if sub['day'] == today_day:
            text = f"🔔 <b>Напоминание об оплате!</b>\nСегодня нужно оплатить: <b>{sub['name']}</b>\nСумма: {sub['amount']}р."
            await bot.send_message(user_id, text, parse_mode="HTML")


# --- ЭКСПОРТ И ГРАФИКИ ---
@dp.message(F.text == "Экспорт")
async def export_to_excel(message: types.Message):
    await message.answer("Формирую Excel файл...")
    df = db.get_all_df()
    if df.empty:
        return await message.answer("Таблица пуста.")
    
    file_path = "expenses.xlsx"
    df.to_excel(file_path, index=False)
    await message.answer_document(FSInputFile(file_path), caption="Ваш отчет в Excel")
    os.remove(file_path)

@dp.message(F.text == "График")
async def send_graph(message: types.Message):
    await message.answer("Создаю график...")
    df = db.get_all_df()
    if df.empty:
        return await message.answer("Нет данных для графика")
    
    df['Стоимость'] = pd.to_numeric(df['Стоимость'], errors='coerce').fillna(0)
    summary = df.groupby('Категория')['Стоимость'].sum()
    
    plt.figure(figsize=(10, 6))
    summary.plot(kind='pie', autopct='%1.1f%%', startangle=140)
    plt.title("Расходы по категориям")
    plt.ylabel("")
    
    graph_path = "graph.png"
    plt.savefig(graph_path)
    plt.close()
    
    await message.answer_photo(FSInputFile(graph_path), caption="Аналитика в графиках")
    os.remove(graph_path)


# --- ПОИСК ---
@dp.message(F.text == "Поиск")
async def search_start(message: types.Message, state: FSMContext):
    await message.answer("Введите название товара или магазина для поиска:", reply_markup=get_cancel_kb())
    await state.set_state(SearchState.waiting_for_query)

@dp.message(SearchState.waiting_for_query)
async def search_process(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)

    df = db.get_all_df()
    query = message.text.lower()
    result = df[df['Название'].str.lower().str.contains(query, na=False) | 
                df['Магазин'].str.lower().str.contains(query, na=False)]
    
    if result.empty:
        await message.answer("Ничего не найдено.", reply_markup=get_expenses_menu())
    else:
        text = "🔍 Результаты поиска:\n\n"
        for _, row in result.tail(10).iterrows(): 
            text += f"• {row['Название']} — {row['Стоимость']}р \n"
        await message.answer(text, reply_markup=get_expenses_menu())
    await state.clear()


#--- УДАЛЕНИЕ ЗАПИСИ ---

@dp.message(DeleteState.selecting_category)
async def list_items_to_delete(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)

    items = db.get_records_by_category(message.text)
    if not items:
        await message.answer("Записей не найдено.", reply_markup=get_expenses_menu())
        await state.clear()
        return

    response = f"Выберите номер для удаления ({message.text}):\n\n"
    buttons = []
    delete_map = {}
    
    for i, item in enumerate(items, 1):
        response += f"{i}. {item.get('Название')} — {item.get('Стоимость')}р\n"
        delete_map[str(i)] = item['row_idx']
        buttons.append([KeyboardButton(text=str(i))])
    
    buttons.append([KeyboardButton(text="Назад")])
    await state.update_data(delete_map=delete_map)
    await state.set_state(DeleteState.selecting_item)
    await message.answer(response, reply_markup=ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True))

@dp.message(DeleteState.selecting_item)
async def confirm_delete(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)

    data = await state.get_data()
    row = data.get('delete_map', {}).get(message.text)
    
    if row and db.delete_by_row(int(row)):
        await message.answer("✅ Удалено.", reply_markup=get_expenses_menu())
    else:
        await message.answer("Ошибка.")
    await state.clear()

# --- ВНЕСЕНИЕ РАСХОДА ---
@dp.message(F.text == "Внести расход")
async def start_expense(message: types.Message):
    await message.answer("Выбери категорию:", reply_markup=get_categories_kb())

@dp.message(F.text.in_(["Продукты", "Развлечения", "Ежемесячные", "Остальное"]))
async def select_category_default(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == DeleteState.selecting_category:
        return 

    await state.set_state(ExpenseForm.category)
    await state.update_data(category=message.text)
    await state.set_state(ExpenseForm.name)
    await message.answer(f"Внесение расхода в {message.text}. Введите название:", reply_markup=get_cancel_kb())
    
@dp.message(ExpenseForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ExpenseForm.price)
    await message.answer("Введите стоимость:")

@dp.message(ExpenseForm.price)
async def process_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите только число!")
    
    if int(message.text) > LIMIT:
        await message.answer(f"⚠️ Внимание! Трата превышает ваш лимит {LIMIT}р!")
        
    await state.update_data(price=message.text)
    await state.set_state(ExpenseForm.shop)
    await message.answer("Магазин (или 'нет'):")

@dp.message(ExpenseForm.shop)
async def process_shop(message: types.Message, state: FSMContext):
    data = await state.get_data()
    shop = message.text if message.text.lower() != 'нет' else "-"
    db.add_expense(data['category'], data['name'], data['price'], shop)
    await message.answer("✅ Записано!", reply_markup=get_expenses_menu())
    await state.clear()


# --- УДАЛЕНИЕ ---
@dp.message(F.text == "Удалить запись")
async def start_delete(message: types.Message, state: FSMContext):
    await state.set_state(DeleteState.selecting_category) 
    await message.answer("В какой категории удалить?", reply_markup=get_categories_kb())


# --- ОТЧЕТЫ И ЛИМИТЫ ---
@dp.message(F.text == "Отчеты")
async def report_cmd(message: types.Message):
    await message.answer(db.get_monthly_analytics())

@dp.message(F.text == "Лимиты")
async def show_limits(message: types.Message, state: FSMContext):
    await message.answer(f"Лимит: {LIMIT}р. Введите новое число:", reply_markup=get_cancel_kb())
    await state.set_state(LimitState.waiting_for_limit)

@dp.message(LimitState.waiting_for_limit)
async def set_limit(message: types.Message, state: FSMContext):
    global LIMIT
    if message.text.isdigit():
        LIMIT = int(message.text)
        await message.answer(f"✅ Лимит изменен: {LIMIT}р", reply_markup=get_settings_menu())
        await state.clear()
    else:
        await message.answer("Введите число.")


# --- ЗАПУСК ---
async def on_startup_notify():
    print("\n" + "="*30 + "\n✅ БОТ ЗАПУЩЕН\n" + "="*30 + "\n")
    
    # Настраиваем еженедельный отчет (Каждое воскресенье в 12:00)
    scheduler.add_job(send_weekly_report, "cron", day_of_week="sun", hour=12, minute=0)
    
    # Настраиваем ежедневную проверку подписок (Каждый день в 10:00)
    scheduler.add_job(check_daily_subscriptions, "cron", hour=10, minute=0)
    
    scheduler.start()

async def main():
    dp.startup.register(on_startup_notify)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Бот выключен")