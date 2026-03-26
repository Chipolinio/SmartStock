import logging
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.db.repositories.AnalyticsRepository import (
    get_sales_history as repo_get_sales_history,
    get_stock_dynamics as repo_get_stock_dynamics,
    get_abc_data as repo_get_abc_data,
    get_xyz_data as repo_get_xyz_data,
    get_top_products_by_revenue as repo_get_top_products_by_revenue,
    get_top_products_by_sales as repo_get_top_products_by_sales,
    get_products_rating as repo_get_products_rating,
    get_dashboard_kpi as repo_get_dashboard_kpi,
    get_low_stock as repo_get_low_stock,
)
from src.db.schemas.Analytics import (
    DashboardBaseRequest,
)
from src.db.schemas.DashboardMetric import (
    SalesDynamicsResponse,
    StockDynamicsResponse,
    ABCAnalysisResponse,
    XYZAnalysisResponse,
    TopProductsByRevenueResponse,
    TopProductsBySalesResponse,
    ProductsRatingResponse,
    DashboardKPIResponse,
    LowStockResponse,
)
from src.db.schemas.Forecast import (
    ProductForecastsResponse,
    ForecastHistoryResponse,
    ForecastSummaryResponse,
)
from src.services import MLService as MLServiceModule

logger = logging.getLogger(__name__)


async def get_sales_dynamics(
    session: AsyncSession,
    user_id: int,
    request: DashboardBaseRequest
) -> SalesDynamicsResponse:
    """Получить динамику продаж и выручки."""
    if request.product_id:
        return await repo_get_sales_history(
            session=session,
            product_id=request.product_id,
            days=request.days
        )

    # Если product_id не указан, возвращаем агрегированные данные по всем товарам пользователя
    return await repo_get_sales_history(
        session=session,
        product_id=None,  # Все товары
        days=request.days,
        user_id=user_id,  # Только товары пользователя
        brand=request.brand,
        subject=request.subject
    )


async def get_stock_dynamics(
    session: AsyncSession,
    user_id: int,
    request: DashboardBaseRequest
) -> StockDynamicsResponse:
    """Получить динамику остатков на складе."""
    if request.product_id:
        return await repo_get_stock_dynamics(
            session=session,
            product_id=request.product_id,
            days=request.days
        )

    # Если product_id не указан, возвращаем агрегированные данные по всем товарам пользователя
    return await repo_get_stock_dynamics(
        session=session,
        product_id=None,  # Все товары
        days=request.days,
        user_id=user_id,  # Только товары пользователя
        brand=request.brand,
        subject=request.subject
    )


async def get_abc_analysis(
    session: AsyncSession,
    user_id: int,
    request: DashboardBaseRequest
) -> ABCAnalysisResponse:
    """Получить ABC-анализ товаров."""
    return await repo_get_abc_data(
        session=session,
        user_id=user_id,
        days=request.days,
        brand=request.brand,
        subject=request.subject
    )


async def get_xyz_analysis(
    session: AsyncSession,
    user_id: int,
    request: DashboardBaseRequest
) -> XYZAnalysisResponse:
    """Получить XYZ-анализ товаров."""
    return await repo_get_xyz_data(
        session=session,
        user_id=user_id,
        days=request.days,
        brand=request.brand,
        subject=request.subject
    )


async def get_top_products_by_revenue(
    session: AsyncSession,
    user_id: int,
    request: DashboardBaseRequest,
    limit: int = 10
) -> TopProductsByRevenueResponse:
    """Получить топ товаров по выручке."""
    return await repo_get_top_products_by_revenue(
        session=session,
        user_id=user_id,
        limit=limit,
        days=request.days,
        brand=request.brand,
        subject=request.subject
    )


async def get_top_products_by_sales(
    session: AsyncSession,
    user_id: int,
    request: DashboardBaseRequest,
    limit: int = 10
) -> TopProductsBySalesResponse:
    """Получить топ товаров по продажам."""
    return await repo_get_top_products_by_sales(
        session=session,
        user_id=user_id,
        limit=limit,
        days=request.days,
        brand=request.brand,
        subject=request.subject
    )


async def get_products_rating(
    session: AsyncSession,
    user_id: int,
    request: DashboardBaseRequest,
    limit: int = 10
) -> ProductsRatingResponse:
    """Получить рейтинг товаров по оценкам."""
    return await repo_get_products_rating(
        session=session,
        user_id=user_id,
        limit=limit,
        days=request.days,
        brand=request.brand,
        subject=request.subject
    )


async def get_dashboard_kpi(
    session: AsyncSession,
    user_id: int,
    request: DashboardBaseRequest
) -> DashboardKPIResponse:
    """Получить сводные KPI дашборда."""
    return await repo_get_dashboard_kpi(
        session=session,
        user_id=user_id,
        days=request.days
    )


async def get_low_stock(
    session: AsyncSession,
    user_id: int,
    limit: int = 10
) -> LowStockResponse:
    """Получить товары с низким остатком."""
    return await repo_get_low_stock(
        session=session,
        user_id=user_id,
        limit=limit
    )


# =============================================================================
# ПРОГНОЗЫ (Forecast Methods)
# =============================================================================

async def get_product_forecasts(
    session: AsyncSession,
    user_id: int,
    request: DashboardBaseRequest
) -> ProductForecastsResponse:
    """Получить прогнозы по всем избранным товарам."""
    return await MLServiceModule.get_product_forecasts(
        session=session,
        user_id=user_id,
        days=request.days,
        brand=request.brand,
        subject=request.subject
    )


async def get_forecast_history(
    session: AsyncSession,
    user_id: int,
    days: int = 30,
    product_id: int | None = None
) -> ForecastHistoryResponse:
    """Получить историю прогнозов продаж."""
    if not product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="product_id is required for forecast history"
        )
    return await MLServiceModule.get_forecast_history(
        session=session,
        product_id=product_id,
        limit=days
    )


async def get_forecast_summary(
    session: AsyncSession,
    user_id: int
) -> ForecastSummaryResponse:
    """Получить сводную статистику по прогнозам."""
    return await MLServiceModule.get_forecast_summary(
        session=session,
        user_id=user_id
    )
