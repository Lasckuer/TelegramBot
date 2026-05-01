import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import BOT_TOKEN
from gsheets import GoogleTable

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = GoogleTable()

# Состояния FSM
class ExpenseForm(StatesGroup):
    category = State()
    name = State()
    price = State()
    shop = State()

def get_main_kb():
    buttons = [
        [KeyboardButton(text="Продукты"), KeyboardButton(text="Развлечения")],
        [KeyboardButton(text="Ежемесячные расходы"), KeyboardButton(text="Остальное")],
        [KeyboardButton(text="Вывести весь список")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Выберите категорию расходов:", reply_markup=get_main_kb())

@dp.message(F.text == "Вывести весь список")
async def show_list(message: types.Message):
    data = db.get_all_data()
    await message.answer(data)

@dp.message(F.text.in_(["Продукты", "Развлечения", "Ежемесячные расходы", "Остальное"]))
async def select_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(ExpenseForm.name)
    await message.answer(f"Выбрано: {message.text}. Введите название товара/услуги:")

@dp.message(ExpenseForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ExpenseForm.price)
    await message.answer("Введите стоимость:")

@dp.message(ExpenseForm.price)
async def process_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Пожалуйста, введите число.")
    
    await state.update_data(price=message.text)
    await state.set_state(ExpenseForm.shop)
    await message.answer("Введите название магазина (или напишите 'нет'):")

@dp.message(ExpenseForm.shop)
async def process_shop(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    shop = message.text if message.text.lower() != 'нет' else "-"
    
    result = db.add_expense(
        user_data['category'], 
        user_data['name'], 
        user_data['price'], 
        shop
    )
    
    if result == "exists":
        await message.answer("Такой товар с такой же ценой уже добавлен в таблицу!", reply_markup=get_main_kb())
    else:
        await message.answer("Данные успешно внесены в Google Таблицу.", reply_markup=get_main_kb())
    
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())