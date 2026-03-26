from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.db.database import get_db
from src.db.schemas.Product import ProductResponse, ProductDetailedResponse
from src.services import ProductService as ProductServiceModule

router = APIRouter()


# =============================================================================
# ТОВАРЫ (GET — только чтение)
# =============================================================================

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = Query(default=0, ge=0, description="Пропуск (пагинация)"),
    limit: int = Query(default=100, ge=1, le=1000, description="Лимит записей"),
    name: str | None = Query(None, min_length=2, description="Поиск по названию"),
    brand: str | None = Query(None, description="Фильтр по бренду"),
    subject: str | None = Query(None, description="Фильтр по категории"),
    entity: str | None = Query(None, description="Фильтр по типу"),
    session: AsyncSession = Depends(get_db)
):
    """
    Получить список товаров с фильтрацией.
    
    - **skip**: пропуск записей (пагинация)
    - **limit**: количество записей (макс. 1000)
    - **name**: поиск по названию (частичное совпадение)
    - **brand**: фильтр по бренду (точное совпадение)
    - **subject**: фильтр по категории (точное совпадение)
    - **entity**: фильтр по типу сущности
    """
    return await ProductServiceModule.get_products_filter(
        session=session,
        skip=skip,
        limit=limit,
        name=name,
        brand=brand,
        subject=subject,
        entity=entity
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_db)
):
    """
    Получить информацию о товаре по ID (артикулу WB).

    - **product_id**: артикул товара на маркетплейсе
    """
    try:
        return await ProductServiceModule.get_product_by_id(
            product_id=product_id,
            session=session
        )
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Товар с артикулом {product_id} не найден"
            )
        raise


@router.get("/{product_id}/detailed", response_model=ProductDetailedResponse)
async def get_product_detailed(
    product_id: int,
    session: AsyncSession = Depends(get_db)
):
    """
    Получить полную информацию о товаре для страницы аналитики.
    Включает цену, остатки, рейтинг, продажи и другую статистику.

    - **product_id**: артикул товара на маркетплейсе
    """
    return await ProductServiceModule.get_product_detailed(
        product_id=product_id,
        session=session
    )
