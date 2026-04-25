from fastapi import APIRouter

from app.api.routes.forecasting import router as forecasting_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.orders import router as orders_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.suppliers import router as suppliers_router

api_router = APIRouter()
api_router.include_router(suppliers_router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(inventory_router, prefix="/inventory", tags=["inventory"])
api_router.include_router(forecasting_router, prefix="/forecasting", tags=["forecasting"])
api_router.include_router(
    recommendations_router,
    prefix="/recommendations",
    tags=["recommendations"],
)
api_router.include_router(orders_router, prefix="/orders", tags=["orders"])
