import os
import json
import math
import pandas as pd
import matplotlib.pyplot as plt
from aiogram import Router, F, Bot, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton

import keyboards as kb
from states import ExpenseForm, DeleteState, LimitState, SearchState, SubState
from gsheets import GoogleTable
from qr_scanner import decode_qr, fetch_receipt_data

router = Router()
db = GoogleTable()

LIMIT = 50000
SUBS_FILE = "subs.json"

def load_subs():
    if not os.path.exists(SUBS_FILE):
        return []
    with open(SUBS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_subs(subs):
    with open(SUBS_FILE, 'w', encoding='utf-8') as f:
        json.dump(subs, f, ensure_ascii=False, indent=4)

# ==========================================
# --- НАВИГАЦИЯ ПО МЕНЮ ---
# ==========================================
@router.message(Command("start"))
@router.message(F.text == "Назад")
async def main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=kb.get_main_menu())

@router.message(F.text == "Расходы")
async def expenses_menu(message: types.Message):
    await message.answer("Раздел 'Расходы':", reply_markup=kb.get_expenses_menu())

@router.message(F.text == "Настройки")
async def settings_menu(message: types.Message):
    await message.answer("Раздел 'Настройки':", reply_markup=kb.get_settings_menu())

# ==========================================
# --- УВЕДОМЛЕНИЯ О ПОДПИСКАХ ---
# ==========================================
@router.message(F.text == "Уведомления")
async def setup_notifications(message: types.Message, state: FSMContext):
    subs = load_subs()
    text = "🗓 Ваши текущие подписки/платежи:\n"
    if not subs:
        text += "Пусто.\n"
    else:
        for s in subs:
            text += f"🔹 {s['name']} — {s['amount']}р (День оплаты: {s['day']}-го числа)\n"
    
    text += "\nЧтобы добавить новое уведомление, введите название подписки:"
    await message.answer(text, reply_markup=kb.get_cancel_kb())
    await state.set_state(SubState.waiting_for_name)

@router.message(SubState.waiting_for_name)
async def sub_name_process(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)
    await state.update_data(name=message.text)
    await message.answer("Введите сумму платежа (число):")
    await state.set_state(SubState.waiting_for_amount)

@router.message(SubState.waiting_for_amount)
async def sub_amount_process(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Пожалуйста, введите только число.")
    await state.update_data(amount=int(message.text))
    await message.answer("В какой день месяца присылать уведомление? (число от 1 до 31):")
    await state.set_state(SubState.waiting_for_day)

@router.message(SubState.waiting_for_day)
async def sub_day_process(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (1 <= int(message.text) <= 31):
        return await message.answer("Введите корректный день (число от 1 до 31).")
    
    data = await state.get_data()
    new_sub = {"name": data['name'], "amount": data['amount'], "day": int(message.text)}
    subs = load_subs()
    subs.append(new_sub)
    save_subs(subs)
    
    await message.answer(f"✅ Напоминание сохранено!\n{new_sub['name']} ({new_sub['amount']}р) — {new_sub['day']}-го числа каждого месяца.", reply_markup=kb.get_settings_menu())
    await state.clear()

# ==========================================
# --- ЭКСПОРТ И ГРАФИКИ ---
# ==========================================
@router.message(F.text == "Экспорт")
async def export_to_excel(message: types.Message):
    await message.answer("Формирую Excel файл...")
    df = db.get_all_df()
    if df.empty:
        return await message.answer("Таблица пуста.")
    
    file_path = "expenses.xlsx"
    df.to_excel(file_path, index=False)
    await message.answer_document(FSInputFile(file_path), caption="Ваш отчет в Excel")
    if os.path.exists(file_path):
        os.remove(file_path)

@router.message(F.text == "График")
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
    if os.path.exists(graph_path):
        os.remove(graph_path)

# ==========================================
# --- ПОИСК ---
# ==========================================
@router.message(F.text == "Поиск")
async def search_start(message: types.Message, state: FSMContext):
    await message.answer("Введите название товара или магазина для поиска:", reply_markup=kb.get_cancel_kb())
    await state.set_state(SearchState.waiting_for_query)

def generate_page_text(matches: list, query: str, page: int, per_page: int = 5):
    """Вспомогательная функция для генерации текста одной страницы"""
    import math
    total_pages = math.ceil(len(matches) / per_page)
    start = page * per_page
    end = start + per_page
    page_items = matches[start:end]

    text = f"🔍 Результаты по запросу «{query}» (Стр. {page+1} из {total_pages}):\n\n"
    for row in page_items:
        date_str = row.get('Дата', '-')
        text += f"• <b>{row.get('Название', '-')}</b> — {row.get('Стоимость', 0)}р <i>({date_str})</i>\n"

    markup = kb.get_pagination_kb(page, total_pages)
    return text, markup

@router.message(SearchState.waiting_for_query)
async def search_process(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)

    df = db.get_all_df()
    if df.empty:
        await message.answer("Таблица расходов пока пуста.", reply_markup=kb.get_expenses_menu())
        return await state.clear()

    query = message.text.lower()
    if 'Название' not in df.columns: df['Название'] = ""
    if 'Магазин' not in df.columns: df['Магазин'] = ""

    result = df[
        df['Название'].astype(str).str.lower().str.contains(query, na=False) | 
        df['Магазин'].astype(str).str.lower().str.contains(query, na=False)
    ]
    
    if result.empty:
        await message.answer("Ничего не найдено.", reply_markup=kb.get_expenses_menu())
        return await state.clear()
    
    matches = result.to_dict('records')
    await state.update_data(search_results=matches, query=query)
    
    text, markup = generate_page_text(matches, query, page=0)
    await message.answer(text, reply_markup=markup, parse_mode="HTML")

@router.callback_query(F.data.startswith("page_"))
async def process_page_callback(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])
    
    data = await state.get_data()
    matches = data.get("search_results", [])
    query = data.get("query", "")

    if not matches:
        return await callback.answer("Данные устарели. Сделайте поиск заново.", show_alert=True)

    text, markup = generate_page_text(matches, query, page)
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    await callback.answer()

# ==========================================
# --- Удаление записей ---
# ==========================================
@router.message(DeleteState.selecting_category)
async def list_items_to_delete(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)

    items = db.get_records_by_category(message.text)
    if not items:
        await message.answer("Записей не найдено.", reply_markup=kb.get_expenses_menu())
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

@router.message(DeleteState.selecting_item)
async def confirm_delete(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)

    data = await state.get_data()
    row = data.get('delete_map', {}).get(message.text)
    
    if row and db.delete_by_row(int(row)):
        await message.answer("✅ Удалено.", reply_markup=kb.get_expenses_menu())
    else:
        await message.answer("Ошибка.")
    await state.clear()

# ==========================================
# --- ВНЕСЕНИЕ РАСХОДА (РУЧНОЕ) ---
# ==========================================
@router.message(F.text == "Внести расход")
async def start_expense(message: types.Message):
    await message.answer("Выбери категорию:", reply_markup=kb.get_categories_kb())

@router.message(F.text.in_(["Продукты", "Развлечения", "Ежемесячные", "Остальное"]))
async def select_category_default(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == DeleteState.selecting_category:
        return 

    await state.set_state(ExpenseForm.category)
    await state.update_data(category=message.text)
    await state.set_state(ExpenseForm.name)
    await message.answer(f"Внесение расхода в {message.text}. Введите название:", reply_markup=kb.get_cancel_kb())
    
@router.message(ExpenseForm.name)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)
    await state.update_data(name=message.text)
    await state.set_state(ExpenseForm.price)
    await message.answer("Введите стоимость:")

@router.message(ExpenseForm.price)
async def process_price(message: types.Message, state: FSMContext):
    if not message.text.replace('.','',1).isdigit():
        return await message.answer("Введите только число!")
    
    if float(message.text) > LIMIT:
        await message.answer(f"⚠️ Внимание! Трата превышает ваш лимит {LIMIT}р!")
        
    await state.update_data(price=message.text)
    await state.set_state(ExpenseForm.shop)
    await message.answer("Магазин (или 'нет'):")

@router.message(ExpenseForm.shop)
async def process_shop(message: types.Message, state: FSMContext):
    data = await state.get_data()
    shop = message.text if message.text.lower() != 'нет' else "-"
    db.add_expense(data['category'], data['name'], data['price'], shop)
    await message.answer("✅ Записано!", reply_markup=kb.get_expenses_menu())
    await state.clear()

# ==========================================
# --- ВНЕСЕНИЕ РАСХОДА (QR ЧЕК) ---
# ==========================================
@router.message(F.text == "Отсканировать чек")
async def ask_for_receipt(message: types.Message, state: FSMContext):
    # Эта функция реагирует на кнопку "Отсканировать чек"
    # На всякий случай очищаем FSM, чтобы бот точно ждал фото
    await state.clear()
    await message.answer("Отправь мне фотографию QR-кода с чека (без сжатия или крупным планом).", reply_markup=kb.get_cancel_kb())

@router.message(F.photo)
async def handle_receipt_photo(message: types.Message, bot: Bot):
    # Эта функция реагирует на присланное фото
    await message.answer("⏳ Анализирую QR-код...")
    photo = message.photo[-1]
    file_path = f"temp_{photo.file_id}.jpg"
    await bot.download(photo, destination=file_path)
    
    qr_string = decode_qr(file_path)
    if os.path.exists(file_path):
        os.remove(file_path) 
    
    if not qr_string:
        return await message.answer("❌ Не удалось найти или прочитать QR-код на фото. Попробуй сфоткать крупнее.", reply_markup=kb.get_expenses_menu())
    
    await message.answer("🔍 QR найден! Запрашиваю данные из ФНС (это может занять до 15 секунд)...")
    
    try:
        receipt_data = await fetch_receipt_data(qr_string)
        
        if not receipt_data:
            return await message.answer("❌ Сервис проверки чеков недоступен или превышено время ожидания.", reply_markup=kb.get_expenses_menu())
        
        if receipt_data.get('code') != 1:
            error_msg = receipt_data.get('data', 'Неизвестная ошибка') if isinstance(receipt_data.get('data'), str) else 'Чек не найден'
            return await message.answer(f"❌ Ошибка ФНС: {error_msg}\nВозможно, чек еще не попал в базу. Попробуй позже.", reply_markup=kb.get_expenses_menu())
        
        items = receipt_data['data']['json']['items']
        added_count = 0
        total_sum = 0
        shop_name = receipt_data['data']['json'].get('user') or receipt_data['data']['json'].get('retailPlace', 'Магазин из чека')
        
        for item in items:
            name = item.get('name', 'Неизвестный товар')
            price = math.ceil(int(item.get('sum', 0)) / 100)
            
            db.add_expense(category="Продукты", name=name, price=price, shop=shop_name)
            added_count += 1
            total_sum += price
            
        await message.answer(f"✅ Успешно добавлено {added_count} позиций из магазина «{shop_name}»!\nНа общую сумму: {total_sum}р.", reply_markup=kb.get_expenses_menu())
        
    except KeyError as e:
        print(f"Ошибка ключа (нетипичный чек): {e}")
        await message.answer("❌ Не удалось разобрать структуру товаров в этом чеке.", reply_markup=kb.get_expenses_menu())
    except Exception as e:
        print(f"Непредвиденная ошибка в чеке: {e}")
        await message.answer("❌ Произошла ошибка при обработке данных чека.", reply_markup=kb.get_expenses_menu())
        
# ==========================================
# --- УДАЛЕНИЕ ЗАПИСИ ---
# ==========================================
@router.message(F.text == "Удалить запись")
async def start_delete(message: types.Message, state: FSMContext):
    await state.set_state(DeleteState.selecting_category) 
    await message.answer("В какой категории удалить?", reply_markup=kb.get_categories_kb())

# ==========================================
# --- ОТЧЕТЫ И ЛИМИТЫ ---
# ==========================================
@router.message(F.text == "Отчеты")
async def report_cmd(message: types.Message):
    await message.answer(db.get_monthly_analytics())

@router.message(F.text == "Лимиты")
async def show_limits(message: types.Message, state: FSMContext):
    await message.answer(f"Лимит: {LIMIT}р. Введите новое число:", reply_markup=kb.get_cancel_kb())
    await state.set_state(LimitState.waiting_for_limit)

@router.message(LimitState.waiting_for_limit)
async def set_limit(message: types.Message, state: FSMContext):
    global LIMIT
    if message.text.isdigit():
        LIMIT = int(message.text)
        await message.answer(f"✅ Лимит изменен: {LIMIT}р", reply_markup=kb.get_settings_menu())
        await state.clear()
    else:
        await message.answer("Введите число.")
        
# ==========================================
# --- СРАВНЕНИЕ МЕСЯЦЕВ ---
# ==========================================
@router.message(F.text == "Сравнение")
async def compare_months(message: types.Message):
    from datetime import datetime
    
    df = db.get_all_df()
    if df.empty or 'Дата' not in df.columns:
        return await message.answer("Нет данных для сравнения. Сначала внесите расходы.")

    df['Дата_dt'] = pd.to_datetime(df['Дата'], format="%d.%m.%Y", errors='coerce')
    df['Стоимость'] = pd.to_numeric(df['Стоимость'], errors='coerce').fillna(0)

    now = datetime.now()
    curr_month, curr_year = now.month, now.year
    
    if curr_month == 1:
        prev_month, prev_year = 12, curr_year - 1
    else:
        prev_month, prev_year = curr_month - 1, curr_year

    curr_df = df[(df['Дата_dt'].dt.month == curr_month) & (df['Дата_dt'].dt.year == curr_year)]
    prev_df = df[(df['Дата_dt'].dt.month == prev_month) & (df['Дата_dt'].dt.year == prev_year)]

    curr_grouped = curr_df.groupby('Категория')['Стоимость'].sum()
    prev_grouped = prev_df.groupby('Категория')['Стоимость'].sum()

    all_categories = set(curr_grouped.index).union(set(prev_grouped.index))

    if not all_categories:
        return await message.answer("В этом и прошлом месяце нет трат для сравнения.")

    text = "📊 <b>Сравнение с прошлым месяцем:</b>\n\n"
    total_curr = curr_grouped.sum()
    total_prev = prev_grouped.sum()

    for cat in all_categories:
        curr_val = curr_grouped.get(cat, 0)
        prev_val = prev_grouped.get(cat, 0)

        if prev_val == 0 and curr_val > 0:
            text += f"🔹 <b>{cat}</b>: {curr_val}р (В прошлом месяце трат не было)\n"
        elif curr_val == 0 and prev_val > 0:
            text += f"🔹 <b>{cat}</b>: 0р (Траты упали на 100%, было {prev_val}р)\n"
        else:
            diff = curr_val - prev_val
            percent = abs(diff) / prev_val * 100
            if diff > 0:
                text += f"🔺 <b>{cat}</b>: {curr_val}р (На {percent:.1f}% больше)\n"
            elif diff < 0:
                text += f"🔻 <b>{cat}</b>: {curr_val}р (На {percent:.1f}% меньше)\n"
            else:
                text += f"➖ <b>{cat}</b>: {curr_val}р (Без изменений)\n"

    text += "\n💰 <b>ИТОГО:</b>\n"
    if total_prev == 0:
        text += f"В этом месяце: {total_curr}р (В прошлом не было трат)"
    else:
        diff_total = total_curr - total_prev
        perc_total = abs(diff_total) / total_prev * 100
        if diff_total > 0:
            text += f"🔺 Вы потратили на <b>{perc_total:.1f}% больше</b> ({total_curr}р против {total_prev}р)"
        elif diff_total < 0:
            text += f"🔻 Вы <b>сэкономили {perc_total:.1f}%</b> ({total_curr}р против {total_prev}р)"
        else:
            text += f"➖ Потрачено ровно столько же ({total_curr}р)"

    await message.answer(text, parse_mode="HTML")