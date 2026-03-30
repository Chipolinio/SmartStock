import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock
from datetime import date, timedelta
from src.services.MLService import (
    run_daily_forecast,
    run_model_training,
    get_product_forecast_summary,
    get_full_analysis,
    get_forecast_history,
    get_product_forecasts,
    get_forecast_summary,
)

class MockRow:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def _asdict(self):
        return self.__dict__


@pytest.mark.asyncio
async def test_run_daily_forecast_empty_data(mocker):
    """Прогноз с пустыми данными."""
    # Arrange
    mock_session = AsyncMock()

    mocker.patch(
        "src.services.MLService.read_features_by_date",
        return_value=[]
    )

    # Act
    result = await run_daily_forecast(mock_session, date.today())

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_run_daily_forecast_no_predicted_column(mocker):
    """Отсутствие колонки predicted_sales."""
    # Arrange
    mock_session = AsyncMock()

    mock_raw = [
        MockRow(
            product_id=101, price=500.0, discount_pct=0.0,
            rating=4.8, feedbacks=50, stock_left=10,
            avg_7d=2.0, avg_14d=2.0, price_rank=1, rating_rank=1,
            price_rank_in_category=1
        )
    ]

    mocker.patch(
        "src.services.MLService.read_features_by_date",
        return_value=mock_raw
    )

    # DataFrame без predicted_sales
    import pandas as pd
    mock_df = pd.DataFrame({'product_id': [101]})  # Нет predicted_sales

    mocker.patch("src.services.MLService.predict_sales_and_oos", return_value=mock_df)

    # Act
    result = await run_daily_forecast(mock_session, date.today())

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_run_model_training_success(mocker):
    """Успешное обучение модели."""
    # Arrange
    mock_session = AsyncMock()

    mock_raw = [
        MockRow(
            ProductFeaturesDaily=MockRow(
                price=500.0, discount_pct=0.0, rating=4.8,
                feedbacks=50, stock_left=10, price_rank_in_category=1
            ),
            real_sales_next_day=5.0
        )
    ]

    mocker.patch(
        "src.services.MLService.get_all_features_for_train",
        return_value=mock_raw
    )
    mocker.patch("src.services.MLService.train_model", return_value=True)

    # Act
    result = await run_model_training(mock_session)

    # Assert
    assert result is True


# =============================================================================
# get_product_forecast_summary
# =============================================================================

@pytest.mark.asyncio
async def test_get_product_forecast_summary_no_prediction(mocker):
    """Нет прогноза для товара."""
    # Arrange
    mock_session = AsyncMock()

    mocker.patch(
        "src.services.MLService.read_latest_prediction",
        return_value=None
    )

    # Act
    result = await get_product_forecast_summary(mock_session, product_id=1)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_product_forecast_summary_success(mocker):
    """Прогноз найден."""
    # Arrange
    mock_session = AsyncMock()

    mock_prediction = MagicMock()
    mock_prediction.product_id = 1
    mock_prediction.dt = date.today()
    mock_prediction.predicted_sales = 10.5
    mock_prediction.model_version = "v1"

    mocker.patch(
        "src.services.MLService.read_latest_prediction",
        return_value=mock_prediction
    )

    # Act
    result = await get_product_forecast_summary(mock_session, product_id=1)

    # Assert
    assert result["product_id"] == 1
    assert result["predicted_sales"] == 10.5
    assert result["model_version"] == "v1"


# =============================================================================
# get_full_analysis
# =============================================================================

@pytest.mark.asyncio
async def test_get_full_analysis_no_features(mocker):
    """Нет текущих характеристик."""
    # Arrange
    mock_session = AsyncMock()

    mock_prediction = MagicMock()
    mock_prediction.predicted_sales = 10.0

    mock_read_latest = AsyncMock(return_value=mock_prediction)
    mock_read_features = AsyncMock(return_value=None)

    mocker.patch(
        "src.services.MLService.read_latest_prediction",
        mock_read_latest
    )
    mocker.patch(
        "src.services.MLService.read_features_latest",
        mock_read_features
    )

    # Act
    result = await get_full_analysis(mock_session, product_id=1)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_full_analysis_success(mocker):
    """Успешный полный анализ."""
    # Arrange
    mock_session = AsyncMock()

    mock_prediction = MagicMock()
    mock_prediction.predicted_sales = 10.0
    mock_prediction.model_version = "v1"
    mock_prediction.dt = date.today()

    mock_features = MagicMock()
    mock_features.stock_left = 100
    mock_features.price = 500.0

    mocker.patch(
        "src.services.MLService.read_latest_prediction",
        return_value=mock_prediction
    )
    mocker.patch(
        "src.services.MLService.read_features_latest",
        return_value=mock_features
    )

    # Act
    result = await get_full_analysis(mock_session, product_id=1)

    # Assert
    assert result["product_id"] == 1
    assert result["current_stock"] == 100
    assert result["prediction"]["days_until_out_of_stock"] == 10.0  # 100 / 10
    assert result["alerts"]["is_low_stock"] is False
    assert result["alerts"]["critical_oos"] is False


@pytest.mark.asyncio
async def test_get_full_analysis_low_stock_alert(mocker):
    """Низкий остаток (alert)."""
    # Arrange
    mock_session = AsyncMock()

    mock_prediction = MagicMock()
    mock_prediction.predicted_sales = 10.0

    mock_features = MagicMock()
    mock_features.stock_left = 50  # 5 дней до OOS
    mock_features.price = 500.0

    mocker.patch(
        "src.services.MLService.read_latest_prediction",
        return_value=mock_prediction
    )
    mocker.patch(
        "src.services.MLService.read_features_latest",
        return_value=mock_features
    )

    # Act
    result = await get_full_analysis(mock_session, product_id=1)

    # Assert
    assert result["alerts"]["is_low_stock"] is True  # < 7 дней
    assert result["alerts"]["critical_oos"] is False


@pytest.mark.asyncio
async def test_get_full_analysis_critical_oos_alert(mocker):
    """Критический OOS (alert)."""
    # Arrange
    mock_session = AsyncMock()

    mock_prediction = MagicMock()
    mock_prediction.predicted_sales = 10.0

    mock_features = MagicMock()
    mock_features.stock_left = 20  # 2 дня до OOS
    mock_features.price = 500.0

    mocker.patch(
        "src.services.MLService.read_latest_prediction",
        return_value=mock_prediction
    )
    mocker.patch(
        "src.services.MLService.read_features_latest",
        return_value=mock_features
    )

    # Act
    result = await get_full_analysis(mock_session, product_id=1)

    # Assert
    assert result["alerts"]["is_low_stock"] is True
    assert result["alerts"]["critical_oos"] is True  # < 3 дня


@pytest.mark.asyncio
async def test_get_full_analysis_zero_predicted_sales(mocker):
    """Нулевой прогноз продаж."""
    # Arrange
    mock_session = AsyncMock()

    mock_prediction = MagicMock()
    mock_prediction.predicted_sales = 0.0

    mock_features = MagicMock()
    mock_features.stock_left = 100
    mock_features.price = 500.0

    mocker.patch(
        "src.services.MLService.read_latest_prediction",
        return_value=mock_prediction
    )
    mocker.patch(
        "src.services.MLService.read_features_latest",
        return_value=mock_features
    )

    # Act
    result = await get_full_analysis(mock_session, product_id=1)

    # Assert
    assert result["prediction"]["days_until_out_of_stock"] == 999  # default


# =============================================================================
# get_forecast_history
# =============================================================================

@pytest.mark.asyncio
async def test_get_forecast_history_success(mocker):
    """История прогнозов."""
    # Arrange
    mock_session = AsyncMock()

    mock_history = [
        MagicMock(
            dt=date.today() - timedelta(days=1),
            predicted_sales=8.0,
            model_version="v1"
        ),
        MagicMock(
            dt=date.today(),
            predicted_sales=10.0,
            model_version="v1"
        ),
    ]

    mocker.patch(
        "src.services.MLService.read_predict_sales_history",
        return_value=mock_history
    )

    # Act
    result = await get_forecast_history(mock_session, product_id=1, limit=30)

    # Assert
    assert result.product_id == 1
    assert len(result.data) == 2
    assert result.data[0].predicted_sales == 8.0
    assert result.data[1].predicted_sales == 10.0


@pytest.mark.asyncio
async def test_get_forecast_history_empty(mocker):
    """Пустая история прогнозов."""
    # Arrange
    mock_session = AsyncMock()

    mocker.patch(
        "src.services.MLService.read_predict_sales_history",
        return_value=[]
    )

    # Act
    result = await get_forecast_history(mock_session, product_id=1, limit=30)

    # Assert
    assert result.product_id == 1
    assert len(result.data) == 0


# =============================================================================
# get_product_forecasts
# =============================================================================

@pytest.mark.asyncio
async def test_get_product_forecasts_no_products(mocker):
    """Нет избранных товаров."""
    # Arrange
    mock_session = AsyncMock()

    mocker.patch(
        "src.services.MLService.read_user_favorites_filtered",
        return_value=[]
    )

    # Act
    result = await get_product_forecasts(mock_session, user_id=1, days=30)

    # Assert
    assert len(result.data) == 0


@pytest.mark.asyncio
async def test_get_product_forecasts_success(mocker):
    """Прогнозы для избранных товаров."""
    # Arrange
    mock_session = AsyncMock()

    mock_product = MagicMock()
    mock_product.product_id = 1
    mock_product.name = "Product 1"
    mock_product.brand = "Brand 1"

    mock_prediction = MagicMock()
    mock_prediction.predicted_sales = 10.0
    mock_prediction.model_version = "v1"
    mock_prediction.dt = date.today()

    mock_features = MagicMock()
    mock_features.stock_left = 100

    mock_history = [
        MagicMock(dt=date.today(), predicted_sales=10.0, model_version="v1")
    ]

    mocker.patch(
        "src.services.MLService.read_user_favorites_filtered",
        return_value=[mock_product]
    )
    mocker.patch(
        "src.services.MLService.read_latest_prediction",
        return_value=mock_prediction
    )
    mocker.patch(
        "src.services.MLService.read_features_latest",
        return_value=mock_features
    )
    mocker.patch(
        "src.services.MLService.read_predict_sales_history",
        return_value=mock_history
    )

    mock_scalar = AsyncMock()
    mock_scalar.scalar_one_or_none = MagicMock(return_value=500.0)
    mock_session.execute = AsyncMock(return_value=mock_scalar)

    # Act
    result = await get_product_forecasts(mock_session, user_id=1, days=30)

    # Assert
    assert len(result.data) == 1
    assert result.data[0].product_id == 1
    assert result.data[0].latest_prediction.sales_next_day == 10.0
    assert result.data[0].latest_prediction.days_until_out_of_stock == 10.0


@pytest.mark.asyncio
async def test_get_product_forecasts_with_filters(mocker):
    """Прогнозы с фильтрами по бренду и категории."""
    # Arrange
    mock_session = AsyncMock()

    mock_read = mocker.patch(
        "src.services.MLService.read_user_favorites_filtered",
        return_value=[]
    )

    # Act
    await get_product_forecasts(
        mock_session, user_id=1, days=30,
        brand="Apple", subject="Electronics"
    )

    # Assert
    mock_read.assert_called_once_with(1, mock_session, brand="Apple", subject="Electronics")


# =============================================================================
# get_forecast_summary
# =============================================================================

@pytest.mark.asyncio
async def test_get_forecast_summary_no_products(mocker):
    """Нет избранных товаров."""
    # Arrange
    mock_session = AsyncMock()

    mocker.patch(
        "src.services.MLService.read_user_favorites",
        return_value=[]
    )

    # Act
    result = await get_forecast_summary(mock_session, user_id=1)

    # Assert
    assert result.total_products == 0
    assert result.avg_predicted_sales == 0.0
    assert result.oos_risk_count == 0


@pytest.mark.asyncio
async def test_get_forecast_summary_success(mocker):
    """Успешная сводка прогнозов."""
    # Arrange
    mock_session = AsyncMock()

    mock_product = MagicMock()
    mock_product.product_id = 1
    mock_product.name = "Product 1"

    mock_prediction = MagicMock()
    mock_prediction.predicted_sales = 10.0

    mock_features = MagicMock()
    mock_features.stock_left = 50  # 5 дней до OOS

    mock_scalar = AsyncMock()
    mock_scalar.scalar_one_or_none = MagicMock(return_value=500.0)
    mock_session.execute = AsyncMock(return_value=mock_scalar)

    mocker.patch(
        "src.services.MLService.read_user_favorites",
        return_value=[mock_product]
    )
    mocker.patch(
        "src.services.MLService.read_latest_prediction",
        return_value=mock_prediction
    )
    mocker.patch(
        "src.services.MLService.read_features_latest",
        return_value=mock_features
    )

    # Act
    result = await get_forecast_summary(mock_session, user_id=1)

    # Assert
    assert result.total_products == 1
    assert result.avg_predicted_sales == 10.0
    assert result.oos_risk_count == 1  # 5 дней < 7
    assert result.items[0].is_oos_risk is True


@pytest.mark.asyncio
async def test_get_forecast_summary_mixed_risks(mocker):
    """Смешанные риски OOS."""
    # Arrange
    mock_session = AsyncMock()

    mock_product1 = MagicMock()
    mock_product1.product_id = 1
    mock_product1.name = "Product 1"

    mock_product2 = MagicMock()
    mock_product2.product_id = 2
    mock_product2.name = "Product 2"

    mock_prediction = MagicMock()
    mock_prediction.predicted_sales = 10.0

    # Товар 1: 50 stock → 5 дней (риск)
    mock_features1 = MagicMock()
    mock_features1.stock_left = 50

    # Товар 2: 200 stock → 20 дней (нет риска)
    mock_features2 = MagicMock()
    mock_features2.stock_left = 200

    mock_scalar = AsyncMock()
    mock_scalar.scalar_one_or_none = MagicMock(return_value=500.0)
    mock_session.execute = AsyncMock(return_value=mock_scalar)

    mocker.patch(
        "src.services.MLService.read_user_favorites",
        return_value=[mock_product1, mock_product2]
    )
    mocker.patch(
        "src.services.MLService.read_latest_prediction",
        return_value=mock_prediction
    )
    mocker.patch(
        "src.services.MLService.read_features_latest",
        side_effect=[mock_features1, mock_features2]
    )

    # Act
    result = await get_forecast_summary(mock_session, user_id=1)

    # Assert
    assert result.total_products == 2
    assert result.oos_risk_count == 1  # Только первый товар
    assert result.items[0].is_oos_risk is True
    assert result.items[1].is_oos_risk is False