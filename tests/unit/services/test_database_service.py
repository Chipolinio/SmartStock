"""
Юнит-тесты для DatabaseService (функциональный подход).

Тестируемые функции:
- fill_daily_dataset() — заполнение ежедневных данных
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date


@pytest.mark.asyncio
async def test_fill_daily_dataset_success(mocker):
    """Успешное заполнение ежедневных данных."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    mock_raw_row = MagicMock()
    mock_raw_row.product_id = 100
    mock_raw_row.price_sale = 1000.0
    mock_raw_row.discount_pct = 10.0
    mock_raw_row.rating = 4.5
    mock_raw_row.feedbacks = 50
    mock_raw_row.quantity = 50
    mock_raw_row.avg_7d = 5.0
    mock_raw_row.avg_14d = 4.5
    mock_raw_row.price_rank = 1
    mock_raw_row.rating_rank = 2

    mocker.patch(
        "src.services.DatabaseService.get_aggregated_features_data",
        return_value=[mock_raw_row]
    )

    mock_bulk_create = mocker.patch(
        "src.services.DatabaseService.create_features_daily_bulk",
        return_value=None
    )

    # Act
    from src.services.DatabaseService import fill_daily_dataset
    await fill_daily_dataset(mock_session, date.today())

    # Assert
    mock_bulk_create.assert_called_once()
    args, _ = mock_bulk_create.call_args
    features = args[0]
    assert len(features) == 1
    assert features[0].product_id == 100
    assert features[0].days_to_oos == 10.0  # stock / avg_7d = 50 / 5


@pytest.mark.asyncio
async def test_fill_daily_dataset_empty_data(mocker):
    """Заполнение с пустыми данными."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mocker.patch(
        "src.services.DatabaseService.get_aggregated_features_data",
        return_value=[]
    )

    mock_bulk_create = mocker.patch(
        "src.services.DatabaseService.create_features_daily_bulk",
        return_value=None
    )

    # Act
    from src.services.DatabaseService import fill_daily_dataset
    await fill_daily_dataset(mock_session, date.today())

    # Assert
    mock_bulk_create.assert_not_called()


@pytest.mark.asyncio
async def test_fill_daily_dataset_null_values(mocker):
    """Заполнение с NULL значениями."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_raw_row = MagicMock()
    mock_raw_row.product_id = 100
    mock_raw_row.price_sale = None
    mock_raw_row.discount_pct = None
    mock_raw_row.rating = None
    mock_raw_row.feedbacks = None
    mock_raw_row.quantity = 0
    mock_raw_row.avg_7d = 0
    mock_raw_row.avg_14d = None
    mock_raw_row.price_rank = None
    mock_raw_row.rating_rank = None

    mocker.patch(
        "src.services.DatabaseService.get_aggregated_features_data",
        return_value=[mock_raw_row]
    )

    mock_bulk_create = mocker.patch(
        "src.services.DatabaseService.create_features_daily_bulk",
        return_value=None
    )

    # Act
    from src.services.DatabaseService import fill_daily_dataset
    await fill_daily_dataset(mock_session, date.today())

    # Assert
    mock_bulk_create.assert_called_once()
    args, _ = mock_bulk_create.call_args
    features = args[0]
    assert features[0].price == 0.0
    assert features[0].discount_pct == 0.0
    assert features[0].rating == 0.0
    assert features[0].feedbacks == 0
    assert features[0].days_to_oos == 999.0  # default при avg_7d = 0


@pytest.mark.asyncio
async def test_fill_daily_dataset_default_date(mocker):
    """Заполнение без указания даты (используется today)."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_raw_row = MagicMock()
    mock_raw_row.product_id = 100
    mock_raw_row.price_sale = 1000.0
    mock_raw_row.discount_pct = 0.0
    mock_raw_row.rating = 4.0
    mock_raw_row.feedbacks = 10
    mock_raw_row.quantity = 100
    mock_raw_row.avg_7d = 10.0
    mock_raw_row.avg_14d = 8.0
    mock_raw_row.price_rank = 1
    mock_raw_row.rating_rank = 1

    mocker.patch(
        "src.services.DatabaseService.get_aggregated_features_data",
        return_value=[mock_raw_row]
    )

    mock_bulk_create = mocker.patch(
        "src.services.DatabaseService.create_features_daily_bulk",
        return_value=None
    )

    # Act
    from src.services.DatabaseService import fill_daily_dataset
    await fill_daily_dataset(mock_session)  # Без target_date

    # Assert
    assert mock_bulk_create.called


@pytest.mark.asyncio
async def test_fill_daily_dataset_days_to_oos_calculation(mocker):
    """Расчёт days_to_oos."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    # Товар 1: stock=100, avg_7d=10 → days_to_oos=10
    mock_raw_row1 = MagicMock()
    mock_raw_row1.product_id = 1
    mock_raw_row1.price_sale = 1000.0
    mock_raw_row1.discount_pct = 0.0
    mock_raw_row1.rating = 4.0
    mock_raw_row1.feedbacks = 10
    mock_raw_row1.quantity = 100
    mock_raw_row1.avg_7d = 10.0
    mock_raw_row1.avg_14d = 8.0
    mock_raw_row1.price_rank = 1
    mock_raw_row1.rating_rank = 1

    # Товар 2: stock=5, avg_7d=5 → days_to_oos=1
    mock_raw_row2 = MagicMock()
    mock_raw_row2.product_id = 2
    mock_raw_row2.price_sale = 500.0
    mock_raw_row2.discount_pct = 0.0
    mock_raw_row2.rating = 3.5
    mock_raw_row2.feedbacks = 5
    mock_raw_row2.quantity = 5
    mock_raw_row2.avg_7d = 5.0
    mock_raw_row2.avg_14d = 4.0
    mock_raw_row2.price_rank = 2
    mock_raw_row2.rating_rank = 2

    mocker.patch(
        "src.services.DatabaseService.get_aggregated_features_data",
        return_value=[mock_raw_row1, mock_raw_row2]
    )

    mock_bulk_create = mocker.patch(
        "src.services.DatabaseService.create_features_daily_bulk",
        return_value=None
    )

    # Act
    from src.services.DatabaseService import fill_daily_dataset
    await fill_daily_dataset(mock_session, date.today())

    # Assert
    args, _ = mock_bulk_create.call_args
    features = args[0]
    assert len(features) == 2
    assert features[0].days_to_oos == 10.0  # 100 / 10
    assert features[1].days_to_oos == 1.0  # 5 / 5


@pytest.mark.asyncio
async def test_fill_daily_dataset_days_to_oos_cap(mocker):
    """days_to_oos ограничен 999."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    # Товар с очень большим stock и маленькими продажами
    mock_raw_row = MagicMock()
    mock_raw_row.product_id = 1
    mock_raw_row.price_sale = 1000.0
    mock_raw_row.discount_pct = 0.0
    mock_raw_row.rating = 4.0
    mock_raw_row.feedbacks = 10
    mock_raw_row.quantity = 10000  # Большой остаток
    mock_raw_row.avg_7d = 0.1  # Маленькие продажи
    mock_raw_row.avg_14d = 0.1
    mock_raw_row.price_rank = 1
    mock_raw_row.rating_rank = 1

    mocker.patch(
        "src.services.DatabaseService.get_aggregated_features_data",
        return_value=[mock_raw_row]
    )

    mock_bulk_create = mocker.patch(
        "src.services.DatabaseService.create_features_daily_bulk",
        return_value=None
    )

    # Act
    from src.services.DatabaseService import fill_daily_dataset
    await fill_daily_dataset(mock_session, date.today())

    # Assert
    args, _ = mock_bulk_create.call_args
    features = args[0]
    assert features[0].days_to_oos == 999.0  # capped at 999
