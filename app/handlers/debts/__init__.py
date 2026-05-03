from aiogram import Router
from .menu import router as menu_router
from .subscriptions import router as subscriptions_router
from .add import router as add_router
from .manage import router as manage_router

debts_router = Router()

debts_router.include_router(menu_router)
debts_router.include_router(subscriptions_router)
debts_router.include_router(add_router)
debts_router.include_router(manage_router)