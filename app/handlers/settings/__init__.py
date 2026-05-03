from aiogram import Router
from .limits import router as limits_router
from .notifications import router as notifications_router
from .export import router as export_router

settings_router = Router()

settings_router.include_router(limits_router)
settings_router.include_router(notifications_router)
settings_router.include_router(export_router)