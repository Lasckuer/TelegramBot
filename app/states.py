from aiogram.fsm.state import State, StatesGroup

# --- Расходы ---
class ExpenseForm(StatesGroup):
    category = State()
    name = State()
    price = State()
    shop = State()
    confirm = State()

class EditExpState(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_new_price = State()

class SearchState(StatesGroup):
    waiting_for_query = State()

# --- Доходы ---
class IncomeForm(StatesGroup):
    category = State()
    name = State()
    price = State()
    confirm = State()

class EditIncState(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_new_price = State()

# --- Долги ---
class DebtForm(StatesGroup):
    person = State()
    amount = State()
    deadline = State()

# --- Настройки и утилиты ---
class LimitState(StatesGroup):
    waiting_for_limit = State()

class SubState(StatesGroup):
    waiting_for_name = State()
    waiting_for_amount = State()
    waiting_for_day = State()

class ExportState(StatesGroup):
    start_date = State()
    end_date = State()