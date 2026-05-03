from aiogram import Router
from .base import router as base_router
from .navigation import router as navigation_router

common_router = Router()

common_router.include_router(base_router)
common_router.include_router(navigation_router)