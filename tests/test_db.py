import pytest
from app.database.db_manager import DatabaseManager

@pytest.fixture
def db():
    test_db = DatabaseManager(db_path=":memory:")
    return test_db

def test_add_expense_logic(db):
    db.add_expense(user_id=123, category="Продукты", name="Хлеб", price=50, shop="Пятерочка")
    
    df = db.get_all_df(user_id=123)
    assert len(df) == 1
    assert df.iloc[0]['name'] == "Хлеб"
    assert df.iloc[0]['price'] == 50

def test_add_income_logic(db):
    db.add_income(user_id=123, source="Зарплата", name="Аванс", amount=15000)
    
    df = db.get_all_incomes(user_id=123)
    assert len(df) == 1
    assert df.iloc[0]['amount'] == 15000