from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
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
from src.services import AnalyticsService as AnalyticsServiceModule
from src.utils.dependencies import get_user

router = APIRouter()


@router.get(
    "/sales-dynamics",
    response_model=SalesDynamicsResponse,
    summary="Динамика продаж",
    description="Временной ряд продаж и выручки по дням"
)
async def get_sales_dynamics(
    days: int = Query(default=30, ge=1, le=365, description="Период в днях"),
    product_id: int | None = Query(None, gt=0, description="Фильтр по товару"),
    brand: str | None = Query(None, description="Фильтр по бренду"),
    subject: str | None = Query(None, description="Фильтр по категории"),
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить динамику продаж и выручки."""
    request = DashboardBaseRequest(
        days=days,
        product_id=product_id,
        brand=brand,
        subject=subject
    )
    return await AnalyticsServiceModule.get_sales_dynamics(
        session=session,
        user_id=user_data["user_id"],
        request=request
    )


@router.get(
    "/stock-dynamics",
    response_model=StockDynamicsResponse,
    summary="Динамика остатков",
    description="Временной ряд остатков на складе по дням"
)
async def get_stock_dynamics(
    days: int = Query(default=30, ge=1, le=365, description="Период в днях"),
    product_id: int | None = Query(None, gt=0, description="Фильтр по товару"),
    brand: str | None = Query(None, description="Фильтр по бренду"),
    subject: str | None = Query(None, description="Фильтр по категории"),
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить динамику остатков на складе."""
    request = DashboardBaseRequest(
        days=days,
        product_id=product_id,
        brand=brand,
        subject=subject
    )
    return await AnalyticsServiceModule.get_stock_dynamics(
        session=session,
        user_id=user_data["user_id"],
        request=request
    )


@router.get(
    "/abc-analysis",
    response_model=ABCAnalysisResponse,
    summary="ABC-анализ",
    description="Классификация товаров по доле выручки (A - 80%, B - 15%, C - 5%)"
)
async def get_abc_analysis(
    days: int = Query(default=30, ge=1, le=365, description="Период в днях"),
    product_id: int | None = Query(None, gt=0, description="Фильтр по товару"),
    brand: str | None = Query(None, description="Фильтр по бренду"),
    subject: str | None = Query(None, description="Фильтр по категории"),
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить ABC-анализ товаров."""
    request = DashboardBaseRequest(
        days=days,
        product_id=product_id,
        brand=brand,
        subject=subject
    )
    return await AnalyticsServiceModule.get_abc_analysis(
        session=session,
        user_id=user_data["user_id"],
        request=request
    )


@router.get(
    "/xyz-analysis",
    response_model=XYZAnalysisResponse,
    summary="XYZ-анализ",
    description="Классификация товаров по стабильности спроса (X - стабильные, Y - колебания, Z - нестабильные)"
)
async def get_xyz_analysis(
    days: int = Query(default=30, ge=1, le=365, description="Период в днях"),
    product_id: int | None = Query(None, gt=0, description="Фильтр по товару"),
    brand: str | None = Query(None, description="Фильтр по бренду"),
    subject: str | None = Query(None, description="Фильтр по категории"),
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить XYZ-анализ товаров."""
    request = DashboardBaseRequest(
        days=days,
        product_id=product_id,
        brand=brand,
        subject=subject
    )
    return await AnalyticsServiceModule.get_xyz_analysis(
        session=session,
        user_id=user_data["user_id"],
        request=request
    )


@router.get(
    "/top-products-by-revenue",
    response_model=TopProductsByRevenueResponse,
    summary="Топ товаров по выручке",
    description="Рейтинг товаров по сумме выручки"
)
async def get_top_products_by_revenue(
    days: int = Query(default=30, ge=1, le=365, description="Период в днях"),
    limit: int = Query(default=10, ge=1, le=100, description="Количество товаров"),
    brand: str | None = Query(None, description="Фильтр по бренду"),
    subject: str | None = Query(None, description="Фильтр по категории"),
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить топ товаров по выручке."""
    request = DashboardBaseRequest(
        days=days,
        product_id=None,
        brand=brand,
        subject=subject
    )
    return await AnalyticsServiceModule.get_top_products_by_revenue(
        session=session,
        user_id=user_data["user_id"],
        request=request,
        limit=limit
    )


@router.get(
    "/top-products-by-sales",
    response_model=TopProductsBySalesResponse,
    summary="Топ товаров по продажам",
    description="Рейтинг товаров по количеству продаж"
)
async def get_top_products_by_sales(
    days: int = Query(default=30, ge=1, le=365, description="Период в днях"),
    limit: int = Query(default=10, ge=1, le=100, description="Количество товаров"),
    brand: str | None = Query(None, description="Фильтр по бренду"),
    subject: str | None = Query(None, description="Фильтр по категории"),
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить топ товаров по продажам."""
    request = DashboardBaseRequest(
        days=days,
        product_id=None,
        brand=brand,
        subject=subject
    )
    return await AnalyticsServiceModule.get_top_products_by_sales(
        session=session,
        user_id=user_data["user_id"],
        request=request,
        limit=limit
    )


@router.get(
    "/products-rating",
    response_model=ProductsRatingResponse,
    summary="Рейтинг товаров",
    description="Рейтинг товаров по средней оценке покупателей"
)
async def get_products_rating(
    days: int = Query(default=30, ge=1, le=365, description="Период в днях"),
    limit: int = Query(default=10, ge=1, le=100, description="Количество товаров"),
    brand: str | None = Query(None, description="Фильтр по бренду"),
    subject: str | None = Query(None, description="Фильтр по категории"),
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить рейтинг товаров по оценкам."""
    request = DashboardBaseRequest(
        days=days,
        product_id=None,
        brand=brand,
        subject=subject
    )
    return await AnalyticsServiceModule.get_products_rating(
        session=session,
        user_id=user_data["user_id"],
        request=request,
        limit=limit
    )


@router.get(
    "/kpi",
    response_model=DashboardKPIResponse,
    summary="KPI дашборда",
    description="Общие метрики: выручка, продажи, рейтинг, количество товаров, доставка"
)
async def get_dashboard_kpi(
    days: int = Query(default=30, ge=1, le=365, description="Период в днях"),
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить сводные KPI дашборда."""
    request = DashboardBaseRequest(
        days=days,
        product_id=None,
        brand=None,
        subject=None
    )
    return await AnalyticsServiceModule.get_dashboard_kpi(
        session=session,
        user_id=user_data["user_id"],
        request=request
    )


@router.get(
    "/low-stock",
    response_model=LowStockResponse,
    summary="Товары с низким остатком",
    description="Товары с риском out-of-stock: критичные (< 7 дней) и предупреждения (< 14 дней)"
)
async def get_low_stock(
    limit: int = Query(default=10, ge=1, le=100, description="Количество товаров"),
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить товары с низким остатком."""
    return await AnalyticsServiceModule.get_low_stock(
        session=session,
        user_id=user_data["user_id"],
        limit=limit
    )


# =============================================================================
# ПРОГНОЗЫ (Forecast Endpoints)
# =============================================================================

@router.get(
    "/forecasts",
    response_model=ProductForecastsResponse,
    summary="Прогнозы по товарам",
    description="Последние прогнозы продаж по всем избранным товарам"
)
async def get_product_forecasts(
    days: int = Query(default=30, ge=1, le=365, description="Период в днях"),
    product_id: int | None = Query(None, gt=0, description="Фильтр по товару"),
    brand: str | None = Query(None, description="Фильтр по бренду"),
    subject: str | None = Query(None, description="Фильтр по категории"),
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить прогнозы продаж по всем избранным товарам."""
    request = DashboardBaseRequest(
        days=days,
        product_id=product_id,
        brand=brand,
        subject=subject
    )
    return await AnalyticsServiceModule.get_product_forecasts(
        session=session,
        user_id=user_data["user_id"],
        request=request
    )


@router.get(
    "/forecasts/history",
    response_model=ForecastHistoryResponse,
    summary="История прогнозов",
    description="История прогнозов продаж за период"
)
async def get_forecast_history(
    days: int = Query(default=30, ge=1, le=365, description="Период в днях"),
    product_id: int | None = Query(None, gt=0, description="Фильтр по товару"),
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить историю прогнозов продаж."""
    return await AnalyticsServiceModule.get_forecast_history(
        session=session,
        user_id=user_data["user_id"],
        days=days,
        product_id=product_id
    )


@router.get(
    "/forecasts/summary",
    response_model=ForecastSummaryResponse,
    summary="Сводка по прогнозам",
    description="Общая статистика по прогнозам: количество товаров, средний прогноз, выручка, тревоги"
)
async def get_forecast_summary(
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить сводную статистику по прогнозам."""
    return await AnalyticsServiceModule.get_forecast_summary(
        session=session,
        user_id=user_data["user_id"]
    )
