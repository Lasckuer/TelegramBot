from aiogram import Router

from .common import common_router
from .expenses import expenses_router
from .incomes import incomes_router
from .debts import debts_router
from .analytics import analytics_router
from .settings import settings_router
from .admin import admin_router

def get_handlers_router() -> Router:
    router = Router()
    router.include_routers(
        common_router,
        expenses_router,
        incomes_router,
        debts_router,
        analytics_router,
        settings_router,
        admin_router
    )
    return router