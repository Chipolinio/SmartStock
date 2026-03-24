from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.db.database import get_db
from src.db.schemas.StockTS import StockTSResponse
from src.db.schemas.SalesProxyTS import SalesProxyTSResponse
from src.db.schemas.PriceTS import PriceTSResponse
from src.db.schemas.DeliveryTS import DeliveryTSResponse
from src.db.schemas.SocialTS import SocialTSResponse
from src.db.schemas.PredictedSalesTS import PredictedSalesTSResponse
from src.services import SalesService as SalesServiceModule

router = APIRouter()


# =============================================================================
# ИСТОРИЯ ДАННЫХ (GET — только чтение)
# =============================================================================

@router.get("/stock/{product_id}", response_model=List[StockTSResponse])
async def get_stock_history(
    product_id: int,
    limit: int = Query(default=30, ge=1, le=365, description="Количество записей"),
    session: AsyncSession = Depends(get_db)
):
    """История остатков товара."""
    return await SalesServiceModule.get_stock_history(
        product_id=product_id,
        session=session,
        limit=limit
    )


@router.get("/sale/{product_id}", response_model=List[SalesProxyTSResponse])
async def get_sales_history(
    product_id: int,
    limit: int = Query(default=30, ge=1, le=365, description="Количество записей"),
    session: AsyncSession = Depends(get_db)
):
    """История продаж товара."""
    return await SalesServiceModule.get_sales_history(
        product_id=product_id,
        session=session,
        limit=limit
    )


@router.get("/price/{product_id}", response_model=List[PriceTSResponse])
async def get_prices_history(
    product_id: int,
    limit: int = Query(default=30, ge=1, le=365, description="Количество записей"),
    session: AsyncSession = Depends(get_db)
):
    """История цен товара."""
    return await SalesServiceModule.get_prices_history(
        product_id=product_id,
        session=session,
        limit=limit
    )


@router.get("/delivery/{product_id}", response_model=List[DeliveryTSResponse])
async def get_deliveries_history(
    product_id: int,
    limit: int = Query(default=30, ge=1, le=365, description="Количество записей"),
    session: AsyncSession = Depends(get_db)
):
    """История доставки товара."""
    return await SalesServiceModule.get_deliveries_history(
        product_id=product_id,
        session=session,
        limit=limit
    )


@router.get("/social/{product_id}", response_model=List[SocialTSResponse])
async def get_socials_history(
    product_id: int,
    limit: int = Query(default=30, ge=1, le=365, description="Количество записей"),
    session: AsyncSession = Depends(get_db)
):
    """История социальных данных товара (рейтинг, отзывы)."""
    return await SalesServiceModule.get_socials_history(
        product_id=product_id,
        session=session,
        limit=limit
    )


@router.get("/predicted_sale/{product_id}", response_model=List[PredictedSalesTSResponse])
async def get_predicted_sales_history(
    product_id: int,
    limit: int = Query(default=30, ge=1, le=365, description="Количество записей"),
    session: AsyncSession = Depends(get_db)
):
    """История прогнозов продаж товара."""
    return await SalesServiceModule.get_predicted_sales_history(
        product_id=product_id,
        session=session,
        limit=limit
    )


@router.get("/analytics/{product_id}")
async def get_product_sales_analytics(
    product_id: int,
    session: AsyncSession = Depends(get_db)
):
    """
    Аналитика по товару: velocity, текущие остатки, дней до OOS.
    
    Returns:
        {
            "velocity": float,  # Средние продажи в день
            "current_stock": int,  # Текущие остатки
            "days_to_oos": int  # Дней до обнуления склада
        }
    """
    return await SalesServiceModule.get_product_analytics(
        product_id=product_id,
        session=session
    )
