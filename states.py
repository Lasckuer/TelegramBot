from aiogram.fsm.state import State, StatesGroup

class ExpenseForm(StatesGroup):
    category = State()
    name = State()
    price = State()
    shop = State()

class DeleteState(StatesGroup):
    selecting_category = State()
    selecting_item = State()

class LimitState(StatesGroup):
    waiting_for_limit = State()

class SearchState(StatesGroup):
    waiting_for_query = State()

class SubState(StatesGroup):
    waiting_for_name = State()
    waiting_for_amount = State()
    waiting_for_day = State()