import pytest
import os
import json
import pandas as pd
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, ANY, patch
from app.handlers import common, expenses, incomes, analytics, settings, debts
from app.jobs import check_daily_subscriptions
from app.handlers.utils import load_json, save_json
from aiogram.types import FSInputFile
from app.states import ExportState

@pytest.mark.asyncio
async def test_main_menu_buttons():
    message = AsyncMock()
    state = AsyncMock()
    
    message.text = "💸 Расходы"
    await common.expenses_menu(message, state)
    message.answer.assert_called_with(ANY, reply_markup=ANY, parse_mode="HTML")
    state.clear.assert_called()

    message.text = "📊 Аналитика"
    await common.analytics_menu(message, state)
    assert "Финансовая сводка" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_expense_management_delete():
    callback = AsyncMock()
    callback.data = "delconfirm_5"
    
    with MagicMock() as mocked_db:
        expenses.db = mocked_db 
        await expenses.execute_delete_inline(callback)
        
        mocked_db.delete_by_row.assert_called_with(5, callback.from_user.id)
        callback.message.edit_text.assert_called_with("✅ Запись удалена.")

@pytest.mark.asyncio
async def test_income_flow():
    message = AsyncMock()
    message.from_user.id = 12345
    message.text = "5000"
    state = AsyncMock()
    state.get_data.return_value = {"source": "Зарплата", "name": "Премия"}
    
    await incomes.process_income_amount(message, state)
    
    state.clear.assert_called_once()
    assert "Доход успешно записан" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_settings_limit():
    message = AsyncMock()
    message.text = "100000"
    state = AsyncMock()
    
    await settings.set_limit(message, state)
    
    assert "Лимит изменен: 100000р" in message.answer.call_args[0][0]
    state.clear.assert_called_once()

@pytest.mark.asyncio
async def test_debts_list():
    callback = AsyncMock()
    
    await debts.list_debts(callback)
    
    args = callback.message.edit_text.call_args[0][0]
    assert ("Активные долги" in args) or ("нет активных долгов" in args)
    
@pytest.mark.asyncio
async def test_edit_name():
    message = AsyncMock()
    message.from_user.id = 12345
    message.text = "Новое название"
    state = AsyncMock()
    state.get_data.return_value = {"edit_row": 5}
    
    await expenses.edit_name_process(message, state)
    # Проверяем вызов с правильными строковыми именами колонок
    expenses.db.update_cell.assert_called_with(5, "name", "Новое название", 12345)
    
@pytest.mark.asyncio
async def test_search_logic():
    message = AsyncMock()
    message.from_user.id = 12345
    message.text = "хлеб"
    state = AsyncMock()
    
    mock_data = pd.DataFrame({
        'name': ['Хлеб Бородинский', 'Молоко'],
        'price': [50, 100],
        'category': ['Продукты', 'Продукты'],
        'shop': ['Пятерочка', 'Магнит'],
        'date': ['01.05.2026', '02.05.2026']
    })
    
    with MagicMock() as mocked_db:
        expenses.db = mocked_db
        mocked_db.get_all_df.return_value = mock_data
        await expenses.search_process(message, state)
        
        mocked_db.get_all_df.assert_called_with(12345)
        assert "Результаты по запросу" in message.answer.call_args[0][0]
        
@pytest.mark.asyncio
async def test_edit_price_process():
    message = AsyncMock()
    message.from_user.id = 12345
    message.text = "150"
    state = AsyncMock()
    state.get_data.return_value = {"edit_row": 10}
    
    with MagicMock() as mocked_db:
        expenses.db = mocked_db
        await expenses.edit_price_process(message, state)
        
        mocked_db.update_cell.assert_called_with(10, "price", 150, 12345)
        state.clear.assert_called_once()

@pytest.mark.asyncio
async def test_analytics_balance():
    callback = AsyncMock()
    callback.from_user.id = 12345
    
    with MagicMock() as mocked_db:
        analytics.db = mocked_db
        await analytics.show_balance(callback)
        
        mocked_db.get_balance_report.assert_called_with(12345)
        callback.message.edit_text.assert_called()
        
@pytest.mark.asyncio
async def test_excel_export_flow():
    callback = AsyncMock()
    callback.from_user.id = 12345
    state = AsyncMock()
    state.get_data.return_value = {'start_date': datetime(2026, 5, 1)}
    
    mock_df = pd.DataFrame({
        'date': ['01.05.2026', '02.05.2026'], 
        'name': ['Хлеб', 'Кофе'],
        'price': [100, 200],
        'category': ['Продукты', 'Продукты'],
        'shop': ['Пятерочка', 'Пятерочка']
    })
    
    with patch('pandas.DataFrame.to_excel') as mock_to_excel, \
         patch('app.handlers.settings.db.get_all_df') as mock_get_df, \
         patch('app.handlers.settings.FSInputFile'), \
         patch('os.path.exists', return_value=True), \
         patch('os.remove'):
        
        mock_get_df.return_value = mock_df
        state.get_state.return_value = ExportState.end_date.state
        
        from app.handlers.settings import calendar_day
        callback.data = "calendar_day_2026_5_10"
        await calendar_day(callback, state)
        
        mock_to_excel.assert_called()
        callback.message.answer_document.assert_called()

@pytest.mark.asyncio
async def test_chart_generation():
    callback = AsyncMock()
    
    import pandas as pd
    mock_df = pd.DataFrame({'category': ['Еда'], 'price': [100]})
    
    with patch('matplotlib.pyplot.savefig') as mock_save, \
         patch('app.handlers.analytics.db.get_all_df') as mock_get_df, \
         patch('app.handlers.analytics.FSInputFile'), \
         patch('os.remove'):
        
        mock_get_df.return_value = mock_df
        await analytics.send_graph(callback)
        
        mock_save.assert_called_with("graph.png")
        callback.message.answer_photo.assert_called()

@pytest.mark.asyncio
async def test_daily_subscriptions_job():
    bot = AsyncMock()
    test_subs = [{"name": "Netflix", "amount": 100, "day": 2, "user_id": 123}]
    
    with patch('app.jobs.load_subs', return_value=test_subs), \
         patch('datetime.datetime') as mock_date:
        
        mock_date.now.return_value.day = 2
        await check_daily_subscriptions(bot)
        
        bot.send_message.assert_called_with(123, ANY, parse_mode="HTML", reply_markup=ANY)

def test_json_integrity_check(tmp_path):
    d = tmp_path / "subdir"
    d.mkdir()
    file = d / "test.json"
    
    data = {"key": "value"}
    save_json(str(file), data)
    assert load_json(str(file)) == data
    
    assert load_json("non_existent.json") == []
    
@pytest.mark.asyncio
async def test_search_logic_fixed():
    message = AsyncMock()
    message.from_user.id = 12345
    message.text = "хлеб"
    state = AsyncMock()
    
    mock_data = pd.DataFrame({
        'name': ['Хлеб Бородинский', 'Молоко'],
        'price': [50, 100],
        'category': ['Продукты', 'Продукты'],
        'shop': ['Пятерочка', 'Магнит'],
        'date': ['01.05.2026', '02.05.2026']
    })
    
    with MagicMock() as mocked_db:
        expenses.db = mocked_db
        mocked_db.get_all_df.return_value = mock_data
        
        await expenses.search_process(message, state)
        
        mocked_db.get_all_df.assert_called_with(12345)
        assert "Результаты по запросу" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_excel_export_column_fix():
    callback = AsyncMock()
    callback.from_user.id = 12345
    state = AsyncMock()
    state.get_data.return_value = {'start_date': datetime(2026, 1, 1)}
    
    mock_df = pd.DataFrame({'date': ['01.01.2026'], 'price': [100]})
    
    with patch('pandas.DataFrame.to_excel') as mock_to_excel, \
         patch('app.handlers.settings.db.get_all_df') as mock_get_df, \
         patch('app.handlers.settings.FSInputFile'), \
         patch('os.path.exists', return_value=True), \
         patch('os.remove'):
        
        mock_get_df.return_value = mock_df
        state.get_state.return_value = ExportState.end_date.state
        
        from app.handlers.settings import calendar_day
        callback.data = "calendar_day_2026_1_10"
        await calendar_day(callback, state)
        
        mock_to_excel.assert_called()

@pytest.mark.asyncio
async def test_analytics_compare_columns():
    callback = AsyncMock()
    callback.from_user.id = 12345
    
    now = datetime.now()
    date_curr = now.strftime("%d.%m.%Y")
    
    mock_df = pd.DataFrame({
        'date': [date_curr, '01.01.1990'],
        'price': [100, 200],
        'category': ['Продукты', 'Продукты'],
        'name': ['Хлеб', 'Старое'],
        'shop': ['Пятерочка', 'Пятерочка']
    })
    
    with MagicMock() as mocked_db:
        analytics.db = mocked_db
        mocked_db.get_all_df.return_value = mock_df
        await analytics.compare_months(callback)
        
        assert callback.message.edit_text.called or callback.answer.called