import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, ANY, patch
from app.handlers import common, expenses, incomes, analytics, settings, debts
from app.states import ExpenseForm, IncomeForm, EditExpState, EditIncState, ExportState
from app.handlers.utils import load_json, save_json
from app.states import DebtForm, IncomeForm, ExpenseForm
from app.jobs import check_daily_debts, check_daily_subscriptions

@pytest.mark.asyncio
async def test_main_menu_routing():
    message = AsyncMock()
    state = AsyncMock()
    await common.main_menu(message, state)
    state.clear.assert_called_once()
    message.answer.assert_called_with(ANY, reply_markup=ANY)

@pytest.mark.asyncio
async def test_expense_add_flow():
    callback = AsyncMock()
    callback.data = "addcat_Продукты"
    state = AsyncMock()
    await expenses.select_category_inline(callback, state)
    state.update_data.assert_called_with(category="Продукты")
    state.set_state.assert_called_with(ExpenseForm.name)
    message = AsyncMock()
    message.text = "Молоко"
    await expenses.process_name(message, state)
    state.update_data.assert_called_with(name="Молоко")
    state.set_state.assert_called_with(ExpenseForm.price)
    message.text = "100"
    message.from_user.id = 1
    with patch('app.handlers.expenses.db') as mock_db:
        mock_db.get_user_limit.return_value = 50000
        await expenses.process_price(message, state)
        state.update_data.assert_called_with(price="100")
        state.set_state.assert_called_with(ExpenseForm.shop)

@pytest.mark.asyncio
async def test_expense_price_invalid():
    message = AsyncMock()
    message.text = "сто рублей"
    state = AsyncMock()
    await expenses.process_price(message, state)
    assert "число" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_income_add_flow():
    callback = AsyncMock()
    callback.data = "addinc_Зарплата"
    state = AsyncMock()
    await incomes.select_income_category(callback, state)
    state.update_data.assert_called_with(category="Зарплата")
    state.set_state.assert_called_with(IncomeForm.name)
    message = AsyncMock()
    message.text = "Фриланс"
    await incomes.process_income_name(message, state)
    state.update_data.assert_called_with(name="Фриланс")
    message.text = "15000"
    message.from_user.id = 1
    state.get_data.return_value = {"category": "Зарплата", "name": "Фриланс"}
    with patch('app.handlers.incomes.db') as mock_db:
        await incomes.process_income_price(message, state)
        mock_db.add_income.assert_called_with(1, "Зарплата", "Фриланс", 15000)
        state.clear.assert_called_once()

@pytest.mark.asyncio
async def test_expense_manage_edit_price():
    message = AsyncMock()
    message.text = "250"
    message.from_user.id = 1
    state = AsyncMock()
    state.get_data.return_value = {"edit_row": 5}
    with patch('app.handlers.expenses.db') as mock_db:
        await expenses.edit_price_process(message, state)
        mock_db.update_cell.assert_called_with(5, "price", 250, 1)
        state.clear.assert_called_once()

@pytest.mark.asyncio
async def test_income_manage_edit_name():
    message = AsyncMock()
    message.text = "Новый проект"
    message.from_user.id = 1
    state = AsyncMock()
    state.get_data.return_value = {"edit_row": 3, "edit_table": "incomes"}
    with patch('app.handlers.incomes.db') as mock_db:
        await incomes.edit_income_name_process(message, state)
        mock_db.update_cell.assert_called_with(3, "name", "Новый проект", 1, table="incomes")
        state.clear.assert_called_once()

@pytest.mark.asyncio
async def test_expense_delete():
    callback = AsyncMock()
    callback.data = "delconfirm_10"
    callback.from_user.id = 1
    with patch('app.handlers.expenses.db') as mock_db:
        await expenses.execute_delete_inline(callback)
        mock_db.delete_by_row.assert_called_with(10, 1)

@pytest.mark.asyncio
async def test_income_delete():
    callback = AsyncMock()
    callback.data = "incdelconfirm_7"
    callback.from_user.id = 1
    with patch('app.handlers.incomes.db') as mock_db:
        await incomes.execute_delete_income(callback)
        mock_db.delete_by_row.assert_called_with(7, 1, table="incomes")

@pytest.mark.asyncio
async def test_expense_search():
    message = AsyncMock()
    message.text = "молоко"
    message.from_user.id = 1
    state = AsyncMock()
    mock_df = pd.DataFrame({'name': ['Молоко 1л', 'Хлеб'], 'shop': ['Ашан', 'Пятерочка'], 'price': [90, 50], 'date': ['01.01.2026', '01.01.2026']})
    with patch('app.handlers.expenses.db') as mock_db:
        mock_db.get_all_df.return_value = mock_df
        await expenses.search_process(message, state)
        state.update_data.assert_called()
        assert "Молоко 1л" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_expense_search_empty():
    message = AsyncMock()
    message.text = "машина"
    message.from_user.id = 1
    state = AsyncMock()
    mock_df = pd.DataFrame({'name': [], 'shop': [], 'price': [], 'date': []})
    with patch('app.handlers.expenses.db') as mock_db:
        mock_db.get_all_df.return_value = mock_df
        await expenses.search_process(message, state)
        assert "пуста" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_set_limit_personal():
    message = AsyncMock()
    message.text = "60000"
    message.from_user.id = 1
    state = AsyncMock()
    with patch('app.handlers.settings.db') as mock_db:
        await settings.set_limit(message, state)
        mock_db.set_user_limit.assert_called_with(1, 60000)
        assert "60000" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_analytics_balance_call():
    callback = AsyncMock()
    callback.from_user.id = 1
    with patch('app.handlers.analytics.db') as mock_db:
        mock_db.get_balance_report.return_value = "Баланс: 5000"
        await analytics.show_balance(callback)
        callback.message.edit_text.assert_called_with("Баланс: 5000", parse_mode="HTML", reply_markup=ANY)

@pytest.mark.asyncio
async def test_export_excel():
    callback = AsyncMock()
    callback.from_user.id = 1
    callback.data = "calendar_day_2026_5_30"
    state = AsyncMock()
    state.get_data.return_value = {'start_date': datetime(2026, 5, 1)}
    state.get_state.return_value = ExportState.end_date.state
    mock_df = pd.DataFrame({'date': ['15.05.2026'], 'name': ['Тест'], 'price': [100]})
    with patch('app.handlers.settings.db.get_all_df', return_value=mock_df), \
         patch('pandas.DataFrame.to_excel') as mock_excel, \
         patch('app.handlers.settings.FSInputFile'), \
         patch('os.path.exists', return_value=True), \
         patch('os.remove'):
        from app.handlers.settings import calendar_day
        await calendar_day(callback, state)
        mock_excel.assert_called()
        callback.message.answer_document.assert_called()

@pytest.mark.asyncio
async def test_qr_scanner_success():
    message = AsyncMock()
    message.from_user.id = 1
    message.photo = [MagicMock(file_id="123")]
    bot = AsyncMock()
    
    mock_receipt_data = {
        'code': 1,
        'data': {
            'json': {
                'retailPlace': 'Пятерочка',
                'items': [{'name': 'Хлеб', 'sum': 5000}]
            }
        }
    }
    
    with patch('app.handlers.expenses.decode_qr', return_value="QR_DATA"), \
         patch('app.handlers.expenses.fetch_receipt_data', return_value=mock_receipt_data), \
         patch('app.handlers.expenses.db') as mock_db, \
         patch('os.path.exists', return_value=True), \
         patch('os.remove'):
        
        await expenses.handle_receipt_photo(message, bot)
        mock_db.add_expense.assert_called_once()
        assert "Добавлено товаров: 1" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_qr_scanner_invalid_qr():
    message = AsyncMock()
    message.photo = [MagicMock(file_id="123")]
    bot = AsyncMock()
    
    with patch('app.handlers.expenses.decode_qr', return_value=None), \
         patch('os.path.exists', return_value=True), \
         patch('os.remove'):
        
        await expenses.handle_receipt_photo(message, bot)
        status_msg = message.answer.return_value
        assert "QR-код не найден" in status_msg.edit_text.call_args[0][0]

def test_json_utils(tmp_path):
    test_file = tmp_path / "test_data.json"
    data = {"users": [1, 2, 3]}
    save_json(str(test_file), data)
    loaded = load_json(str(test_file))
    assert loaded == data
    assert load_json("invalid_path.json") == []
    
@pytest.mark.asyncio
async def test_main_menu_routing():
    message = AsyncMock()
    state = AsyncMock()
    await common.main_menu(message, state)
    state.clear.assert_called_once()
    message.answer.assert_called_with(ANY, reply_markup=ANY)
    
@pytest.mark.asyncio
async def test_debt_add_flow():
    message = AsyncMock()
    message.text = "Иван"
    state = AsyncMock()
    await debts.process_debt_person(message, state)
    state.update_data.assert_called_with(person="Иван")
    state.set_state.assert_called_with(DebtForm.amount)
    message.text = "500"
    await debts.process_debt_amount(message, state)
    state.update_data.assert_called_with(amount=500)
    state.set_state.assert_called_with(DebtForm.deadline)

@pytest.mark.asyncio
async def test_analytics_compare_logic():
    callback = AsyncMock()
    callback.from_user.id = 1
    mock_df = pd.DataFrame({'date': [datetime.now().strftime("%d.%m.%Y")], 'category': ['Продукты'], 'price': [1000]})
    with patch('app.handlers.analytics.db.get_all_df', return_value=mock_df):
        await analytics.compare_months(callback)
        assert callback.message.edit_text.called
        assert "Сравнение" in callback.message.edit_text.call_args[0][0]

@pytest.mark.asyncio
async def test_job_daily_debts_notification():
    bot = AsyncMock()
    today = datetime.now().strftime("%d.%m.%Y")
    mock_debts = [{"id": "1", "person": "Иван", "amount": 500, "deadline": today, "user_id": 123}]
    with patch('app.jobs.load_debts', return_value=mock_debts):
        await check_daily_debts(bot)
        assert bot.send_message.called
        bot.send_message.assert_called_with(123, ANY, parse_mode="HTML", reply_markup=ANY)

@pytest.mark.asyncio
async def test_job_daily_subs_notification():
    bot = AsyncMock()
    today_day = datetime.now().day
    mock_subs = [{"name": "Netflix", "amount": 700, "day": today_day, "user_id": 456}]
    with patch('app.jobs.load_subs', return_value=mock_subs):
        await check_daily_subscriptions(bot)
        assert bot.send_message.called
        bot.send_message.assert_called_with(456, ANY, parse_mode="HTML", reply_markup=ANY)

@pytest.mark.asyncio
async def test_income_flow_full():
    callback = AsyncMock()
    callback.data = "addinc_Зарплата"
    state = AsyncMock()
    await incomes.select_income_category(callback, state)
    state.update_data.assert_called_with(category="Зарплата")
    message = AsyncMock()
    message.from_user.id = 1
    message.text = "1000"
    state.get_data.return_value = {"category": "Зарплата", "name": "Оклад"}
    with patch('app.handlers.incomes.db') as mock_db:
        await incomes.process_income_price(message, state)
        mock_db.add_income.assert_called_once()
        state.clear.assert_called_once()