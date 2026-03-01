from fastapi import APIRouter
from src.api.v1.endpoints import products
from src.api.v1.endpoints import sales
from src.api.v1.endpoints import auth
from src.api.v1.endpoints import analytics
from src.api.v1.endpoints import user
from src.api.v1.endpoints import forecast

router = APIRouter()

router.include_router(products.router, prefix="/products", tags=["products"])
router.include_router(sales.router, prefix="/sales", tags=["sales"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
router.include_router(user.router, prefix="/user", tags=["user"])
router.include_router(forecast.router, prefix="/forecast", tags=["forecast"])
