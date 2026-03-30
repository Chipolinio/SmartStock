"""
Юнит-тесты для AnalyticsService (функциональный подход).

Тестируемые функции:
- get_sales_dynamics() — динамика продаж
- get_stock_dynamics() — динамика остатков
- get_abc_analysis() — ABC-анализ
- get_xyz_analysis() — XYZ-анализ
- get_top_products_by_revenue() — топ по выручке
- get_top_products_by_sales() — топ по продажам
- get_products_rating() — рейтинг товаров
- get_dashboard_kpi() — KPI дашборда
- get_low_stock() — товары с низким остатком
- get_product_forecasts() — прогнозы товаров
- get_forecast_history() — история прогнозов
- get_forecast_summary() — сводка прогнозов
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.services.AnalyticsService import (
    get_sales_dynamics,
    get_stock_dynamics,
    get_abc_analysis,
    get_xyz_analysis,
    get_top_products_by_revenue,
    get_top_products_by_sales,
    get_products_rating,
    get_dashboard_kpi,
    get_low_stock,
    get_product_forecasts,
    get_forecast_history,
    get_forecast_summary,
)
from src.db.schemas.Analytics import DashboardBaseRequest


@pytest.mark.asyncio
async def test_get_sales_dynamics_with_product_id(mocker):
    """Динамика продаж для конкретного товара."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    request = DashboardBaseRequest(
        product_id=100,
        days=30,
        brand=None,
        subject=None
    )

    mock_response = MagicMock()
    mock_response.product_id = 100
    mock_response.sales_data = [{"dt": date.today(), "sales": 5}]

    mocker.patch(
        "src.services.AnalyticsService.repo_get_sales_history",
        return_value=mock_response
    )

    # Act
    result = await get_sales_dynamics(mock_session, user_id=1, request=request)

    # Assert
    assert result.product_id == 100


@pytest.mark.asyncio
async def test_get_sales_dynamics_aggregated(mocker):
    """Агрегированная динамика продаж по всем товарам."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    request = DashboardBaseRequest(
        product_id=None,
        days=30,
        brand="Test Brand",
        subject="Electronics"
    )

    mock_response = MagicMock()
    mock_response.sales_data = [{"dt": date.today(), "sales": 10}]

    mocker.patch(
        "src.services.AnalyticsService.repo_get_sales_history",
        return_value=mock_response
    )

    # Act
    result = await get_sales_dynamics(mock_session, user_id=1, request=request)

    # Assert
    assert len(result.sales_data) == 1
    assert result.sales_data[0]["sales"] == 10


@pytest.mark.asyncio
async def test_get_stock_dynamics_with_product_id(mocker):
    """Динамика остатков для конкретного товара."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    request = DashboardBaseRequest(
        product_id=100,
        days=30,
        brand=None,
        subject=None
    )

    mock_response = MagicMock()
    mock_response.stock_data = [{"dt": date.today(), "stock": 50}]

    mocker.patch(
        "src.services.AnalyticsService.repo_get_stock_dynamics",
        return_value=mock_response
    )

    # Act
    result = await get_stock_dynamics(mock_session, user_id=1, request=request)

    # Assert
    assert result.stock_data[0]["stock"] == 50


@pytest.mark.asyncio
async def test_get_stock_dynamics_aggregated(mocker):
    """Агрегированная динамика остатков."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    request = DashboardBaseRequest(
        product_id=None,
        days=30,
        brand=None,
        subject=None
    )

    mock_response = MagicMock()
    mock_response.stock_data = [{"dt": date.today(), "stock": 100}]

    mocker.patch(
        "src.services.AnalyticsService.repo_get_stock_dynamics",
        return_value=mock_response
    )

    # Act
    result = await get_stock_dynamics(mock_session, user_id=1, request=request)

    # Assert
    assert result.stock_data[0]["stock"] == 100


@pytest.mark.asyncio
async def test_get_abc_analysis(mocker):
    """ABC-анализ товаров."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    request = DashboardBaseRequest(
        product_id=None,
        days=30,
        brand=None,
        subject=None
    )

    mock_response = MagicMock()
    mock_response.items = [
        {"product_id": 1, "group": "A", "revenue": 1000},
        {"product_id": 2, "group": "B", "revenue": 500},
        {"product_id": 3, "group": "C", "revenue": 100},
    ]

    mocker.patch(
        "src.services.AnalyticsService.repo_get_abc_data",
        return_value=mock_response
    )

    # Act
    result = await get_abc_analysis(mock_session, user_id=1, request=request)

    # Assert
    assert len(result.items) == 3
    assert result.items[0]["group"] == "A"


@pytest.mark.asyncio
async def test_get_xyz_analysis(mocker):
    """XYZ-анализ товаров."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    request = DashboardBaseRequest(
        product_id=None,
        days=30,
        brand=None,
        subject=None
    )

    mock_response = MagicMock()
    mock_response.items = [
        {"product_id": 1, "group": "X", "cv": 0.1},
        {"product_id": 2, "group": "Y", "cv": 0.3},
        {"product_id": 3, "group": "Z", "cv": 0.6},
    ]

    mocker.patch(
        "src.services.AnalyticsService.repo_get_xyz_data",
        return_value=mock_response
    )

    # Act
    result = await get_xyz_analysis(mock_session, user_id=1, request=request)

    # Assert
    assert len(result.items) == 3
    assert result.items[0]["group"] == "X"


@pytest.mark.asyncio
async def test_get_top_products_by_revenue(mocker):
    """Топ товаров по выручке."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    request = DashboardBaseRequest(
        product_id=None,
        days=30,
        brand=None,
        subject=None
    )

    mock_response = MagicMock()
    mock_response.items = [
        {"product_id": 1, "revenue": 5000},
        {"product_id": 2, "revenue": 3000},
    ]

    mocker.patch(
        "src.services.AnalyticsService.repo_get_top_products_by_revenue",
        return_value=mock_response
    )

    # Act
    result = await get_top_products_by_revenue(mock_session, user_id=1, request=request, limit=2)

    # Assert
    assert len(result.items) == 2
    assert result.items[0]["revenue"] == 5000


@pytest.mark.asyncio
async def test_get_top_products_by_sales(mocker):
    """Топ товаров по продажам."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    request = DashboardBaseRequest(
        product_id=None,
        days=30,
        brand=None,
        subject=None
    )

    mock_response = MagicMock()
    mock_response.items = [
        {"product_id": 1, "sales": 100},
        {"product_id": 2, "sales": 50},
    ]

    mocker.patch(
        "src.services.AnalyticsService.repo_get_top_products_by_sales",
        return_value=mock_response
    )

    # Act
    result = await get_top_products_by_sales(mock_session, user_id=1, request=request, limit=2)

    # Assert
    assert len(result.items) == 2
    assert result.items[0]["sales"] == 100


@pytest.mark.asyncio
async def test_get_products_rating(mocker):
    """Рейтинг товаров."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    request = DashboardBaseRequest(
        product_id=None,
        days=30,
        brand=None,
        subject=None
    )

    mock_response = MagicMock()
    mock_response.items = [
        {"product_id": 1, "rating": 4.9, "reviews": 200},
        {"product_id": 2, "rating": 4.5, "reviews": 100},
    ]

    mocker.patch(
        "src.services.AnalyticsService.repo_get_products_rating",
        return_value=mock_response
    )

    # Act
    result = await get_products_rating(mock_session, user_id=1, request=request, limit=2)

    # Assert
    assert len(result.items) == 2
    assert result.items[0]["rating"] == 4.9


@pytest.mark.asyncio
async def test_get_dashboard_kpi(mocker):
    """KPI дашборда."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    request = DashboardBaseRequest(
        product_id=None,
        days=30,
        brand=None,
        subject=None
    )

    mock_response = MagicMock()
    mock_response.total_revenue = 100000
    mock_response.total_sales = 500
    mock_response.avg_rating = 4.5

    mocker.patch(
        "src.services.AnalyticsService.repo_get_dashboard_kpi",
        return_value=mock_response
    )

    # Act
    result = await get_dashboard_kpi(mock_session, user_id=1, request=request)

    # Assert
    assert result.total_revenue == 100000
    assert result.total_sales == 500


@pytest.mark.asyncio
async def test_get_low_stock(mocker):
    """Товары с низким остатком."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_response = MagicMock()
    mock_response.items = [
        {"product_id": 1, "stock": 5, "days_to_oos": 2},
        {"product_id": 2, "stock": 10, "days_to_oos": 5},
    ]

    mocker.patch(
        "src.services.AnalyticsService.repo_get_low_stock",
        return_value=mock_response
    )

    # Act
    result = await get_low_stock(mock_session, user_id=1, limit=10)

    # Assert
    assert len(result.items) == 2
    assert result.items[0]["days_to_oos"] == 2


@pytest.mark.asyncio
async def test_get_product_forecasts(mocker):
    """Прогнозы по избранным товарам."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    request = DashboardBaseRequest(
        product_id=None,
        days=30,
        brand=None,
        subject=None
    )

    mock_response = MagicMock()
    mock_response.data = [
        {"product_id": 1, "predicted_sales": 10.0},
        {"product_id": 2, "predicted_sales": 5.0},
    ]

    mocker.patch(
        "src.services.AnalyticsService.MLServiceModule.get_product_forecasts",
        return_value=mock_response
    )

    # Act
    result = await get_product_forecasts(mock_session, user_id=1, request=request)

    # Assert
    assert len(result.data) == 2


@pytest.mark.asyncio
async def test_get_forecast_history_missing_product_id(mocker):
    """История прогнозов без product_id."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_forecast_history(mock_session, user_id=1, days=30, product_id=None)

    assert exc_info.value.status_code == 400
    assert "product_id is required" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_forecast_history_success(mocker):
    """История прогнозов успешно."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_response = MagicMock()
    mock_response.product_id = 100
    mock_response.data = [
        {"dt": date.today(), "predicted_sales": 10.0},
    ]

    mocker.patch(
        "src.services.AnalyticsService.MLServiceModule.get_forecast_history",
        return_value=mock_response
    )

    # Act
    result = await get_forecast_history(mock_session, user_id=1, days=30, product_id=100)

    # Assert
    assert result.product_id == 100
    assert len(result.data) == 1


@pytest.mark.asyncio
async def test_get_forecast_summary(mocker):
    """Сводка прогнозов."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_response = MagicMock()
    mock_response.total_products = 5
    mock_response.avg_predicted_sales = 8.5
    mock_response.oos_risk_count = 2

    mocker.patch(
        "src.services.AnalyticsService.MLServiceModule.get_forecast_summary",
        return_value=mock_response
    )

    # Act
    result = await get_forecast_summary(mock_session, user_id=1)

    # Assert
    assert result.total_products == 5
    assert result.oos_risk_count == 2
