import os
import json
import math
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from aiogram import Router, F, Bot, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

import keyboards as kb
from states import ExpenseForm, LimitState, SearchState, SubState, ExportState, IncomeForm, EditState
from gsheets import GoogleTable
from qr_scanner import decode_qr, fetch_receipt_data

router = Router()
db = GoogleTable()

LIMIT = 50000
SUBS_FILE = "subs.json"
CAT_MAP_FILE = "cat_map.json"

def load_cat_map():
    if not os.path.exists(CAT_MAP_FILE):
        return {}
    with open(CAT_MAP_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_cat_map(mapping):
    with open(CAT_MAP_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=4)

def load_subs():
    if not os.path.exists(SUBS_FILE):
        return []
    with open(SUBS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_subs(subs):
    with open(SUBS_FILE, 'w', encoding='utf-8') as f:
        json.dump(subs, f, ensure_ascii=False, indent=4)

def generate_page_text(matches: list, query: str, page: int, per_page: int = 5):
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

# ==========================================
# --- НАВИГАЦИЯ ПО ГЛАВНОМУ МЕНЮ ---
# ==========================================
@router.message(Command("start"))
@router.message(F.text == "Назад")
async def main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=kb.get_main_menu())

@router.message(F.text == "💸 Расходы")
async def expenses_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("<b>Управление расходами:</b>", reply_markup=kb.get_inline_expenses_menu(), parse_mode="HTML")

@router.message(F.text == "💰 Доходы")
async def incomes_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("<b>Управление доходами:</b>", reply_markup=kb.get_inline_incomes_menu(), parse_mode="HTML")

@router.message(F.text == "📊 Аналитика")
async def analytics_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("<b>Финансовая сводка:</b>", reply_markup=kb.get_inline_analytics_menu(), parse_mode="HTML")

@router.message(F.text == "⚙️ Настройки")
async def settings_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("<b>Настройки профиля:</b>", reply_markup=kb.get_inline_settings_menu(), parse_mode="HTML")

# ==========================================
# --- РАСХОДЫ ---
# ==========================================
@router.callback_query(F.data == "menu_add_exp")
async def start_expense(callback: types.CallbackQuery):
    await callback.message.edit_text("Выбери категорию:", reply_markup=kb.get_inline_categories_kb("addcat"))
    await callback.answer()

@router.callback_query(F.data.startswith("addcat_"))
async def select_category_inline(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[1]
    await state.set_state(ExpenseForm.category)
    await state.update_data(category=category)
    await state.set_state(ExpenseForm.name)
    await callback.message.delete()
    await callback.message.answer(f"Внесение расхода в <b>{category}</b>.\nВведите название:", parse_mode="HTML", reply_markup=kb.get_cancel_kb())
    await callback.answer()

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
    
    if shop != "-":
        cmap = load_cat_map()
        cmap[shop.lower().strip()] = data['category']
        save_cat_map(cmap)
        
    await message.answer("✅ Записано!", reply_markup=kb.get_main_menu())
    await state.clear()

@router.callback_query(F.data == "menu_scan_exp")
async def ask_for_receipt(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Отправь мне фотографию QR-кода с чека (без сжатия или крупным планом).", reply_markup=kb.get_cancel_kb())
    await callback.answer()

@router.message(F.photo)
async def handle_receipt_photo(message: types.Message, bot: Bot):
    await message.answer("⏳ Анализирую QR-код...")
    photo = message.photo[-1]
    file_path = f"temp_{photo.file_id}.jpg"
    await bot.download(photo, destination=file_path)
    
    qr_string = decode_qr(file_path)
    if os.path.exists(file_path):
        os.remove(file_path) 
    
    if not qr_string:
        return await message.answer("❌ QR-код не найден.", reply_markup=kb.get_main_menu())
    
    await message.answer("🔍 Запрашиваю данные из ФНС...")
    
    try:
        receipt_data = await fetch_receipt_data(qr_string)
        if not receipt_data or receipt_data.get('code') != 1:
            return await message.answer("❌ Ошибка получения данных чека.", reply_markup=kb.get_main_menu())
        
        items = receipt_data['data']['json']['items']
        added_count = 0
        total_sum = 0
        shop_name = receipt_data['data']['json'].get('user') or receipt_data['data']['json'].get('retailPlace', 'Магазин из чека')
        
        cmap = load_cat_map()
        assigned_cat = cmap.get(shop_name.lower().strip(), "Продукты")
        
        for item in items:
            name = item.get('name', 'Неизвестный товар')
            price = math.ceil(int(item.get('sum', 0)) / 100)
            
            db.add_expense(category=assigned_cat, name=name, price=price, shop=shop_name)
            added_count += 1
            total_sum += price
            
        await message.answer(f"✅ Добавлено {added_count} позиций (Категория: {assigned_cat}).\nНа сумму: {total_sum}р.", reply_markup=kb.get_main_menu())
        
    except Exception:
        await message.answer("❌ Произошла ошибка при обработке.", reply_markup=kb.get_main_menu())

@router.callback_query(F.data == "menu_search_exp")
async def search_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Введите название товара или магазина для поиска:", reply_markup=kb.get_cancel_kb())
    await state.set_state(SearchState.waiting_for_query)
    await callback.answer()

@router.message(SearchState.waiting_for_query)
async def search_process(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)

    df = db.get_all_df()
    if df.empty:
        await message.answer("Таблица расходов пока пуста.", reply_markup=kb.get_main_menu())
        return await state.clear()

    query = message.text.lower()
    if 'Название' not in df.columns: df['Название'] = ""
    if 'Магазин' not in df.columns: df['Магазин'] = ""

    result = df[
        df['Название'].astype(str).str.lower().str.contains(query, na=False) | 
        df['Магазин'].astype(str).str.lower().str.contains(query, na=False)
    ]
    
    if result.empty:
        await message.answer("Ничего не найдено.", reply_markup=kb.get_main_menu())
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

@router.callback_query(F.data == "menu_manage_exp")
async def start_manage_inline(callback: types.CallbackQuery):
    await callback.message.edit_text("В какой категории?", reply_markup=kb.get_inline_categories_kb("mngcat"))
    await callback.answer()

@router.callback_query(F.data.startswith("mngcat_"))
async def show_items_to_manage(callback: types.CallbackQuery):
    category = callback.data.split("_")[1]
    items = db.get_records_by_category(category)
    if not items:
        return await callback.message.edit_text(f"В категории «{category}» пусто.")
    await callback.message.edit_text(f"Последние записи ({category}):", reply_markup=kb.get_inline_manage_items_kb(items))

@router.callback_query(F.data.startswith("manageitem_"))
async def item_actions_inline(callback: types.CallbackQuery):
    row_idx = int(callback.data.split("_")[1])
    await callback.message.edit_text("Что сделать с записью?", reply_markup=kb.get_inline_item_action_kb(row_idx))

@router.callback_query(F.data.startswith("delconfirm_"))
async def execute_delete_inline(callback: types.CallbackQuery):
    row_idx = int(callback.data.split("_")[1])
    db.delete_by_row(row_idx)
    await callback.message.edit_text("✅ Запись удалена.")

@router.callback_query(F.data == "delcancel")
async def cancel_manage_inline(callback: types.CallbackQuery):
    await callback.message.edit_text("Действие отменено.")

@router.callback_query(F.data.startswith("editname_"))
async def edit_name_start(callback: types.CallbackQuery, state: FSMContext):
    row_idx = int(callback.data.split("_")[1])
    await state.update_data(edit_row=row_idx)
    await state.set_state(EditState.waiting_for_new_name)
    await callback.message.delete()
    await callback.message.answer("Введите новое название:", reply_markup=kb.get_cancel_kb())
    await callback.answer()

@router.message(EditState.waiting_for_new_name)
async def edit_name_process(message: types.Message, state: FSMContext):
    data = await state.get_data()
    db.update_cell(data['edit_row'], 2, message.text)
    await message.answer("✅ Название обновлено!", reply_markup=kb.get_main_menu())
    await state.clear()
    
@router.callback_query(F.data.startswith("editprice_"))
async def edit_price_start(callback: types.CallbackQuery, state: FSMContext):
    row_idx = int(callback.data.split("_")[1])
    await state.update_data(edit_row=row_idx)
    await state.set_state(EditState.waiting_for_new_price)
    await callback.message.delete()
    await callback.message.answer("Введите новую цену:", reply_markup=kb.get_cancel_kb())
    await callback.answer()

@router.message(EditState.waiting_for_new_price)
async def edit_price_process(message: types.Message, state: FSMContext):
    data = await state.get_data()
    db.update_cell(data['edit_row'], 3, int(message.text))
    await message.answer("✅ Цена обновлена!", reply_markup=kb.get_main_menu())
    await state.clear()

# ==========================================
# --- ДОХОДЫ ---
# ==========================================
@router.callback_query(F.data == "menu_add_inc")
async def start_income(callback: types.CallbackQuery):
    await callback.message.edit_text("Выбери источник дохода:", reply_markup=kb.get_inline_income_categories_kb("addinc"))
    await callback.answer()

@router.callback_query(F.data.startswith("addinc_"))
async def select_income_source(callback: types.CallbackQuery, state: FSMContext):
    source = callback.data.split("_")[1]
    await state.set_state(IncomeForm.source)
    await state.update_data(source=source)
    await state.set_state(IncomeForm.name)
    await callback.message.delete()
    await callback.message.answer(f"Источник: <b>{source}</b>.\nОт кого или за что этот доход?", parse_mode="HTML", reply_markup=kb.get_cancel_kb())
    await callback.answer()

@router.message(IncomeForm.name)
async def process_income_name(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        return await main_menu(message, state)
    await state.update_data(name=message.text)
    await state.set_state(IncomeForm.amount)
    await message.answer("Введите сумму дохода:")

@router.message(IncomeForm.amount)
async def process_income_amount(message: types.Message, state: FSMContext):
    if not message.text.replace('.', '', 1).isdigit():
        return await message.answer("Введите только число!")
    
    data = await state.get_data()
    db.add_income(data['source'], data['name'], int(float(message.text)))
    await message.answer("✅ Доход успешно записан!", reply_markup=kb.get_main_menu())
    await state.clear()

@router.callback_query(F.data == "menu_manage_inc")
async def manage_inc_stub(callback: types.CallbackQuery):
    await callback.answer("Управление доходами скоро появится ⏳", show_alert=True)

# ==========================================
# --- АНАЛИТИКА ---
# ==========================================
@router.callback_query(F.data == "menu_balance")
async def show_balance(callback: types.CallbackQuery):
    report = db.get_balance_report()
    await callback.message.edit_text(report, parse_mode="HTML", reply_markup=kb.get_inline_analytics_menu())
    await callback.answer()

@router.callback_query(F.data == "menu_chart")
async def send_graph(callback: types.CallbackQuery):
    await callback.message.delete()
    msg = await callback.message.answer("Создаю график...")
    df = db.get_all_df()
    if df.empty:
        await msg.delete()
        return await callback.message.answer("Нет данных для графика", reply_markup=kb.get_main_menu())
    
    df['Стоимость'] = pd.to_numeric(df['Стоимость'], errors='coerce').fillna(0)
    summary = df.groupby('Категория')['Стоимость'].sum()
    
    plt.figure(figsize=(10, 6))
    summary.plot(kind='pie', autopct='%1.1f%%', startangle=140)
    plt.title("Расходы по категориям")
    plt.ylabel("")
    
    graph_path = "graph.png"
    plt.savefig(graph_path)
    plt.close()
    
    await msg.delete()
    await callback.message.answer_photo(FSInputFile(graph_path), caption="Аналитика в графиках", reply_markup=kb.get_main_menu())
    if os.path.exists(graph_path):
        os.remove(graph_path)
    await callback.answer()

@router.callback_query(F.data == "menu_compare")
async def compare_months(callback: types.CallbackQuery):
    from datetime import datetime
    
    df = db.get_all_df()
    if df.empty or 'Дата' not in df.columns:
        await callback.answer("Нет данных для сравнения.", show_alert=True)
        return

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
        await callback.answer("Нет трат за периоды.", show_alert=True)
        return

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

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb.get_inline_analytics_menu())
    await callback.answer()

# ==========================================
# --- НАСТРОЙКИ ---
# ==========================================
@router.callback_query(F.data == "menu_limits")
async def show_limits(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(f"Лимит: {LIMIT}р. Введите новое число:", reply_markup=kb.get_cancel_kb())
    await state.set_state(LimitState.waiting_for_limit)
    await callback.answer()

@router.message(LimitState.waiting_for_limit)
async def set_limit(message: types.Message, state: FSMContext):
    global LIMIT
    if message.text.isdigit():
        LIMIT = int(message.text)
        await message.answer(f"✅ Лимит изменен: {LIMIT}р", reply_markup=kb.get_main_menu())
        await state.clear()
    else:
        await message.answer("Введите число.")

@router.callback_query(F.data == "menu_notifications")
async def setup_notifications(callback: types.CallbackQuery, state: FSMContext):
    subs = load_subs()
    text = "🗓 Ваши текущие подписки/платежи:\n"
    if not subs:
        text += "Пусто.\n"
    else:
        for s in subs:
            text += f"🔹 {s['name']} — {s['amount']}р (День оплаты: {s['day']}-го числа)\n"
    
    text += "\nЧтобы добавить новое уведомление, введите название подписки:"
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=kb.get_cancel_kb())
    await state.set_state(SubState.waiting_for_name)
    await callback.answer()

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
    
    await message.answer(f"✅ Напоминание сохранено!\n{new_sub['name']} ({new_sub['amount']}р) — {new_sub['day']}-го числа каждого месяца.", reply_markup=kb.get_main_menu())
    await state.clear()

@router.callback_query(F.data == "menu_export")
async def export_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите начальную дату для экспорта:", reply_markup=kb.get_calendar_kb())
    await state.set_state(ExportState.start_date)
    await callback.answer()

@router.callback_query(F.data.startswith("calendar_nav_"))
async def calendar_nav(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    year, month = int(parts[2]), int(parts[3])
    await callback.message.edit_reply_markup(reply_markup=kb.get_calendar_kb(year, month))
    await callback.answer()

@router.callback_query(F.data == "calendar_ignore")
async def calendar_ignore(callback: types.CallbackQuery):
    await callback.answer()

@router.callback_query(F.data == "calendar_cancel")
async def calendar_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Экспорт отменен.", reply_markup=kb.get_main_menu())

@router.callback_query(F.data.startswith("calendar_day_"))
async def calendar_day(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    year, month, day = int(parts[2]), int(parts[3]), int(parts[4])
    selected_date = datetime(year, month, day)

    current_state = await state.get_state()

    if current_state == ExportState.start_date.state:
        await state.update_data(start_date=selected_date)
        await callback.message.edit_text(
            f"Начальная дата: {selected_date.strftime('%d.%m.%Y')}\nТеперь выберите конечную дату:",
            reply_markup=kb.get_calendar_kb(year, month)
        )
        await state.set_state(ExportState.end_date)
    
    elif current_state == ExportState.end_date.state:
        data = await state.get_data()
        start_date = data['start_date']
        end_date = selected_date

        if end_date < start_date:
            start_date, end_date = end_date, start_date

        await callback.message.delete()
        await callback.message.answer(f"Формирую отчет с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}...", reply_markup=kb.get_main_menu())
        await state.clear()

        df = db.get_all_df()
        if df.empty or 'Дата' not in df.columns:
            return await callback.message.answer("Таблица пуста или нет колонки с датами.")

        df['Дата_dt'] = pd.to_datetime(df['Дата'], format="%d.%m.%Y", errors='coerce')
        filtered_df = df[(df['Дата_dt'] >= start_date) & (df['Дата_dt'] <= end_date)].copy()
        filtered_df.drop(columns=['Дата_dt'], inplace=True, errors='ignore')

        if filtered_df.empty:
            return await callback.message.answer("За выбранный период нет записей.")

        file_path = f"expenses_{start_date.strftime('%d%m%Y')}_{end_date.strftime('%d%m%Y')}.xlsx"
        filtered_df.to_excel(file_path, index=False)
        await callback.message.answer_document(FSInputFile(file_path), caption="Ваш отчет в Excel")
        
        if os.path.exists(file_path):
            os.remove(file_path)