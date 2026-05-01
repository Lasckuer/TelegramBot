from aiogram.fsm.state import State, StatesGroup

class ExpenseForm(StatesGroup):
    category = State()
    name = State()
    price = State()
    shop = State()

class EditState(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_new_price = State()

class LimitState(StatesGroup):
    waiting_for_limit = State()

class SearchState(StatesGroup):
    waiting_for_query = State()

class SubState(StatesGroup):
    waiting_for_name = State()
    waiting_for_amount = State()
    waiting_for_day = State()

class ExportState(StatesGroup):
    start_date = State()
    end_date = State()