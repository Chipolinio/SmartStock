from fastapi import APIRouter
from src.api.v1.endpoints import products
from src.api.v1.endpoints import sales
from src.api.v1.endpoints import auth

router = APIRouter()

router.include_router(products.router, prefix="/products", tags=["products"])
router.include_router(sales.router, prefix="/sales", tags=["sales"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
