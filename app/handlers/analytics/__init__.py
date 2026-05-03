from aiogram import Router

from .charts import router as charts_router
from .balance import router as balance_router
from .portfolio import router as portfolio_router
from .ai_tips import router as ai_tips_router

analytics_router = Router()

analytics_router.include_router(charts_router)
analytics_router.include_router(balance_router)
analytics_router.include_router(portfolio_router)
analytics_router.include_router(ai_tips_router)