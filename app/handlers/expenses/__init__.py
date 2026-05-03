from aiogram import Router
from .add import router as add_router
from .qr_scan import router as qr_scan_router
from .search import router as search_router
from .manage import router as manage_router
from .reports import router as reports_router

expenses_router = Router()

expenses_router.include_router(add_router)
expenses_router.include_router(qr_scan_router)
expenses_router.include_router(search_router)
expenses_router.include_router(manage_router)
expenses_router.include_router(reports_router)