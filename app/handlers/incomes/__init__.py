from aiogram import Router
from .add import router as add_router
from .manage import router as manage_router

incomes_router = Router()

incomes_router.include_router(add_router)
incomes_router.include_router(manage_router)