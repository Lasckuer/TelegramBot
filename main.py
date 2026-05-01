import asyncio
import io
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Для чеков (нужно: pip install pytesseract Pillow)
try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None

from config import BOT_TOKEN
from gsheets import GoogleTable

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = GoogleTable()
logging.basicConfig(level=logging.INFO)

LIMIT = 50000 # Пример лимита для уведомлений

class LimitState(StatesGroup):
    waiting_for_limit = State()

async def on_startup():
    print("\n" + "="*30)
    print("✅ БОТ УСПЕШНО ЗАПУЩЕН!")
    print("Бот готов к работе и ожидает сообщений.")
    print("="*30 + "\n")

class ExpenseForm(StatesGroup):
    category = State()
    name = State()
    price = State()
    shop = State()
    
class DeleteState(StatesGroup):
    selecting_category = State()
    selecting_item = State()

# --- КЛАВИАТУРЫ ---

def get_main_menu():
    buttons = [
        [KeyboardButton(text="Внести расход"), KeyboardButton(text="Отчеты")],
        [KeyboardButton(text="Удалить запись"), KeyboardButton(text="Лимиты")]
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
    buttons = [
        [KeyboardButton(text="Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
@dp.message(F.text == "Назад")
async def main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=get_main_menu())

@dp.message(F.text == "Внести расход")
async def start_expense(message: types.Message):
    await message.answer("Выбери категорию или пришли фото чека:", reply_markup=get_categories_kb())

@dp.message(F.text == "Отчеты")
async def report_cmd(message: types.Message):
    res = db.get_monthly_analytics()
    await message.answer(res)

@dp.message(F.text == "Удалить запись")
async def start_delete(message: types.Message, state: FSMContext):
    await state.set_state(DeleteState.selecting_category)
    await message.answer("В какой категории вы хотите что-то удалить?", reply_markup=get_categories_kb())

@dp.message(DeleteState.selecting_category)
async def list_items_to_delete(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await main_menu(message, state)
        return

    # Очищаем название категории от эмодзи и лишних пробелов
    # Если на кнопке "🍎 Продукты", то оставим только "Продукты"
    category = message.text.replace("🍎 ", "").replace("🎬 ", "").replace("📅 ", "").replace("⚙️ ", "").strip()
    
    print(f"DEBUG: Ищу в таблице категорию: '{category}'") # Это будет видно в терминале

    items = db.get_records_by_category(category)
    
    if not items:
        await message.answer(f"В категории '{category}' пока нет записей или названия в таблице не совпадают.", 
                             reply_markup=get_main_menu())
        await state.clear()
        return

    response = f"Выбери номер записи в '{category}' для удаления:\n\n"
    buttons = []
    temp_row = []
    delete_map = {}
    
    for i, item in enumerate(items, 1):
        # Используем .get() чтобы бот не падал, если какой-то колонки нет
        name = item.get('Название', 'Без названия')
        price = item.get('Стоимость', 0)
        
        response += f"{i}. {name} — {price}р.\n"
        delete_map[str(i)] = item['row_idx']
        temp_row.append(KeyboardButton(text=str(i)))
        
        if len(temp_row) == 4: # Делаем по 4 кнопки в ряд
            buttons.append(temp_row)
            temp_row = []
    
    if temp_row: buttons.append(temp_row)
    buttons.append([KeyboardButton(text="Назад")])
    
    await state.update_data(delete_map=delete_map)
    await state.set_state(DeleteState.selecting_item)
    
    await message.answer(response, reply_markup=ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True))

@dp.message(DeleteState.selecting_item)
async def confirm_delete(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await main_menu(message, state)
        return

    data = await state.get_data()
    delete_map = data.get('delete_map', {})
    
    row_to_delete = delete_map.get(message.text)
    
    if row_to_delete:
        if db.delete_by_row(int(row_to_delete)):
            await message.answer(f"✅ Запись №{message.text} успешно удалена из таблицы.", reply_markup=get_main_menu())
        else:
            await message.answer("❌ Ошибка при удалении из Google Таблицы.", reply_markup=get_main_menu())
    else:
        await message.answer("Пожалуйста, выбери номер из списка на кнопках.")
        return

    await state.clear()

# Работа с категориями
@dp.message(F.text.in_(["Продукты", "Развлечения", "Ежемесячные", "Остальное"]))
async def select_category(message: types.Message, state: FSMContext):
    # Очищаем текст от любых эмодзи перед сохранением
    category_clean = message.text.replace("🍎 ", "").replace("🎬 ", "").replace("📅 ", "").replace("⚙️ ", "").strip()
    
    await state.update_data(category=category_clean) # Теперь в базу пойдет чистое слово
    await state.set_state(ExpenseForm.name)
    await message.answer(
        f"📝 Категория: {category_clean}\nВведите название товара или услуги:",
        reply_markup=get_cancel_kb()
    )

@dp.message(ExpenseForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ExpenseForm.price)
    await message.answer("Введите стоимость:")

@dp.message(ExpenseForm.price)
async def process_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число!")
    
    # ПРОВЕРКА ЛИМИТА
    if int(message.text) > LIMIT:
        await message.answer(f"⚠️ Внимание! Трата превышает твой разовый лимит в {LIMIT}р!")
        
    await state.update_data(price=message.text)
    await state.set_state(ExpenseForm.shop)
    await message.answer("Магазин (или 'нет'):")

@dp.message(ExpenseForm.shop)
async def process_shop(message: types.Message, state: FSMContext):
    data = await state.get_data()
    db.add_expense(data['category'], data['name'], data['price'], message.text)
    await message.answer("✅ Сохранено!", reply_markup=get_main_menu())
    await state.clear()

# Распознавание чеков (упрощенное)
@dp.message(F.photo)
async def handle_receipt(message: types.Message):
    if not pytesseract:
        return await message.answer("Библиотека для чеков не установлена.")
    
    msg = await message.answer("🔍 Читаю чек...")
    photo = await bot.download(message.photo[-1])
    image = Image.open(photo)
    text = pytesseract.image_to_string(image, lang='rus+eng')
    
    # Тут должна быть сложная логика поиска суммы, пока просто выведем текст
    await msg.edit_text(f"Текст с чека:\n{text[:200]}...\n\nПока я только учусь искать итоговую сумму, введи данные вручную через 'Внести расход'.")

class LimitState(StatesGroup):
    waiting_for_limit = State()

@dp.message(F.text == "Лимиты")
async def show_limits(message: types.Message, state: FSMContext):
    global LIMIT
    await message.answer(f"Текущий лимит: {LIMIT}р\nВведите новое число, чтобы изменить его, или нажмите 'Назад':", 
                         reply_markup=get_cancel_kb())
    await state.set_state(LimitState.waiting_for_limit)

@dp.message(LimitState.waiting_for_limit)
async def set_limit(message: types.Message, state: FSMContext):
    global LIMIT
    if message.text.isdigit():
        LIMIT = int(message.text)
        await message.answer(f"✅ Новый лимит установлен: {LIMIT}р", reply_markup=get_main_menu())
        await state.clear()
    else:
        await message.answer("Пожалуйста, введите целое число.")

async def main():
    dp.startup.register(on_startup)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Бот выключен пользователем")