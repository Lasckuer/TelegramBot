from aiogram import Router
from . import common, expenses, incomes, debts, analytics, settings

def get_handlers_router() -> Router:
    router = Router()
    router.include_routers(
        common.router,
        expenses.router,
        incomes.router,
        debts.router,
        analytics.router,
        settings.router
    )
    return router