from fastapi import APIRouter
from src.api.v1.endpoints import products
from src.api.v1.endpoints import sales

router = APIRouter()

router.include_router(products.router, prefix="/products", tags=["products"])
router.include_router(sales.router, prefix="/sales", tags=["sales"])