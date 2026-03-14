from fastapi import APIRouter

from .auth import router as auth_router
from .clients import router as clients_router
from .orders import router as orders_router
from .payments import router as payments_router
from .users import router as users_router
from .invites import router as invites_router
from .reminders import router as reminders_router
from .activity import router as activity_router
from .export import router as export_router
from .imports import router as imports_router
from .analytics import router as analytics_router
from .products import router as products_router
from .tasks import router as tasks_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(clients_router, prefix="/clients")
api_router.include_router(orders_router, prefix="/orders")
api_router.include_router(payments_router, prefix="/payments")
api_router.include_router(users_router, prefix="/users")
api_router.include_router(invites_router) # Роутер приглашений использует префиксы внутри самого модуля
api_router.include_router(reminders_router, prefix="/reminders")
api_router.include_router(activity_router, prefix="/activity")
api_router.include_router(export_router, prefix="/export")
api_router.include_router(imports_router, prefix="/import")
api_router.include_router(analytics_router, prefix="/analytics")
api_router.include_router(products_router, prefix="/products")
api_router.include_router(tasks_router, prefix="/tasks")
