from fastapi import APIRouter
from src.api.v1.endpoints import products
from src.api.v1.endpoints import sales
from src.api.v1.endpoints import auth
from src.api.v1.endpoints import dashboard
from src.api.v1.endpoints import user
from src.api.v1.endpoints import admin
from src.api.v1.endpoints import analytics

router = APIRouter()

router.include_router(products.router, prefix="/products", tags=["products"])
router.include_router(sales.router, prefix="/sales", tags=["sales"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(user.router, prefix="/user", tags=["user"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
