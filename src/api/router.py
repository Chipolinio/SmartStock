from fastapi import APIRouter
from src.api.v1.endpoints import products

router = APIRouter()

router.include_router(products.router, prefix="/products", tags=["products"])