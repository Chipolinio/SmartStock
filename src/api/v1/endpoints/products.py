from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.db.database import get_db
from src.db.schemas.Product import ProductCreate, ProductUpdate, ProductResponse
from src.serviсes import ProductService

router = APIRouter()

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
        product: ProductCreate,
        session: AsyncSession = Depends(get_db)
):
    return await ProductService.create_product(product = product, session = session)

@router.get("/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
async def get_product(
        product_id: int,
        session: AsyncSession = Depends(get_db),
):
    return await ProductService.get_product_by_id(product_id = product_id, session = session)

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    name: str | None = None,
    brand: str | None = None,
    session: AsyncSession = Depends(get_db)
):
    return await ProductService.get_products_filter(
        session=session, skip=skip, limit=limit, name=name, brand=brand
    )

@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_in: ProductUpdate,
    session: AsyncSession = Depends(get_db)
):
    return await ProductService.update_product(
        product_id=product_id, product=product_in, session=session
    )

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_db)
):
    await ProductService.delete_product(product_id=product_id, session=session)
    return