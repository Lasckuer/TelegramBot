import pytest
from app.database.db_manager import DatabaseManager

@pytest.fixture
def db():
    return DatabaseManager(db_path=":memory:")

def test_add_expense_logic(db):
    db.add_expense(user_id=123, category="Продукты", name="Хлеб", price=50, shop="Пятерочка")
    df = db.get_all_df(user_id=123)
    assert len(df) == 1
    assert df.iloc[0]['name'] == "Хлеб"
    assert df.iloc[0]['price'] == 50

def test_add_income_logic(db):
    db.add_income(user_id=123, category="Зарплата", name="Аванс", price=15000)
    df = db.get_all_df(user_id=123, table="incomes")
    assert len(df) == 1
    assert df.iloc[0]['price'] == 15000

def test_db_expenses_crud(db):
    db.add_expense(1, "Продукты", "Хлеб", 50, "Магнит")
    db.add_expense(1, "Развлечения", "Кино", 300, "ТЦ")
    df = db.get_all_df(1, table="expenses")
    assert len(df) == 2
    records = db.get_records_by_category("Продукты", 1, table="expenses")
    assert len(records) == 1
    assert records[0]["Название"] == "Хлеб"
    row_id = records[0]["row_idx"]
    db.update_cell(row_id, "price", 60, 1, table="expenses")
    updated_records = db.get_records_by_category("Продукты", 1, table="expenses")
    assert updated_records[0]["Стоимость"] == 60
    db.delete_by_row(row_id, 1, table="expenses")
    assert len(db.get_records_by_category("Продукты", 1, table="expenses")) == 0

def test_db_incomes_crud(db):
    db.add_income(1, "Зарплата", "Аванс", 15000)
    df = db.get_all_df(1, table="incomes")
    assert len(df) == 1
    records = db.get_records_by_category("Зарплата", 1, table="incomes")
    assert records[0]["Название"] == "Аванс"
    row_id = records[0]["row_idx"]
    db.update_cell(row_id, "name", "Премия", 1, table="incomes")
    assert db.get_records_by_category("Зарплата", 1, table="incomes")[0]["Название"] == "Премия"

def test_db_limits_and_balance(db):
    db.set_user_limit(1, 100000)
    assert db.get_user_limit(1) == 100000
    db.add_income(1, "Зарплата", "Основа", 50000)
    db.add_expense(1, "Продукты", "Еда", 10000)
    report = db.get_balance_report(1)
    assert "40000" in report
    assert "100000" in report
    
def test_db_crud_operations(db):
    db.add_expense(1, "Продукты", "Хлеб", 50)
    db.add_income(1, "Зарплата", "Аванс", 15000)
    
    exp_df = db.get_all_df(1, table="expenses")
    inc_df = db.get_all_df(1, table="incomes")
    
    assert len(exp_df) == 1
    assert len(inc_df) == 1
    assert inc_df.iloc[0]['price'] == 15000

    row_id = db.get_records_by_category("Продукты", 1)[0]['row_idx']
    db.update_cell(row_id, "price", 60, 1)
    assert db.get_records_by_category("Продукты", 1)[0]['Стоимость'] == 60
    
    db.delete_by_row(row_id, 1)
    assert len(db.get_records_by_category("Продукты", 1)) == 0

def test_db_balance_logic(db):
    db.set_user_limit(1, 70000)
    db.add_income(1, "Зарплата", "Бонус", 10000)
    db.add_expense(1, "Остальное", "Трата", 2000)
    
    report = db.get_balance_report(1)
    assert "8000" in report
    assert "70000" in report