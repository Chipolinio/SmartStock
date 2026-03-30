"""
Юнит-тесты для SalesService.

Тестируемые функции:
- create_stock_ts() — создание записи остатков
- create_sales_proxy_ts() — создание записи продаж
- create_price_ts() — создание записи цены
- get_stock_history() — история остатков
- get_sales_history() — история продаж
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import date

from src.services.SalesService import (
    create_stock_ts,
    create_sales_proxy_ts,
    create_price_ts,
    create_delivery_ts,
    create_social_ts,
    create_predicted_ts,
    get_stock_history,
    get_sales_history,
    get_prices_history,
    get_deliveries_history,
    get_socials_history,
    get_predicted_sales_history,
    calculate_proxy_sales,
    analytics_data,
    get_product_analytics,
    process_full,
)
from src.db.schemas.StockTS import StockTSCreate
from src.db.schemas.SalesProxyTS import SalesProxyTSCreate
from src.db.schemas.PriceTS import PriceTSCreate
from src.db.schemas.DeliveryTS import DeliveryTSCreate
from src.db.schemas.SocialTS import SocialTSCreate
from src.db.schemas.PredictedSalesTS import PredictedSalesTSCreate
from src.db.schemas.DataPack import FullPayload


@pytest.mark.asyncio
async def test_create_stock_ts_success(mocker):
    """Успешное создание записи остатков."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    stock_in = StockTSCreate(
        product_id=100,
        dt=date.today(),
        quantity=50
    )

    mock_stock = MagicMock()
    mock_stock.id = 1
    mock_stock.product_id = 100
    mock_stock.quantity = 50
    mock_stock.dt = date.today()

    mocker.patch(
        "src.services.SalesService.StockRepo.create_stock_record",
        return_value=mock_stock
    )

    # Act
    result = await create_stock_ts(stock_in, mock_session)

    # Assert
    assert result.product_id == 100
    assert result.quantity == 50
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_stock_ts_duplicate(mocker):
    """Создание дублирующейся записи остатков."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock(side_effect=IntegrityError(
        statement="",
        params=None,
        orig=MagicMock()
    ))
    mock_session.rollback = AsyncMock()

    stock_in = StockTSCreate(
        product_id=100,
        dt=date.today(),
        quantity=50
    )

    mocker.patch(
        "src.services.SalesService.StockRepo.create_stock_record",
        side_effect=IntegrityError("", None, MagicMock())
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await create_stock_ts(stock_in, mock_session)

    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail
    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_create_sales_proxy_ts_success(mocker):
    """Успешное создание записи продаж."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    sale_in = SalesProxyTSCreate(
        product_id=100,
        dt=date.today(),
        sales=5,
        confidence=0.9
    )

    mock_sale = MagicMock()
    mock_sale.id = 1
    mock_sale.product_id = 100
    mock_sale.sales = 5
    mock_sale.dt = date.today()
    mock_sale.confidence = 0.9

    mocker.patch(
        "src.services.SalesService.SalesRepo.create_sale_record",
        return_value=mock_sale
    )

    # Act
    result = await create_sales_proxy_ts(sale_in, mock_session)

    # Assert
    assert result.product_id == 100
    assert result.sales == 5
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_sales_proxy_ts_duplicate(mocker):
    """Создание дублирующейся записи продаж."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock(side_effect=IntegrityError(
        statement="",
        params=None,
        orig=MagicMock()
    ))
    mock_session.rollback = AsyncMock()

    sale_in = SalesProxyTSCreate(
        product_id=100,
        dt=date.today(),
        sales=5,
        confidence=0.9
    )

    mocker.patch(
        "src.services.SalesService.SalesRepo.create_sale_record",
        side_effect=IntegrityError("", None, MagicMock())
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await create_sales_proxy_ts(sale_in, mock_session)

    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_price_ts_success(mocker):
    """Успешное создание записи цены."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    price_in = PriceTSCreate(
        product_id=100,
        dt=date.today(),
        price_sale=1000.0,
        discount_pct=10
    )

    mock_price = MagicMock()
    mock_price.id = 1
    mock_price.product_id = 100
    mock_price.price_sale = 1000.0
    mock_price.discount_pct = 10
    mock_price.dt = date.today()

    mocker.patch(
        "src.services.SalesService.PriceRepo.create_price_record",
        return_value=mock_price
    )

    # Act
    result = await create_price_ts(price_in, mock_session)

    # Assert
    assert result.product_id == 100
    assert result.price_sale == 1000.0
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_price_ts_duplicate(mocker):
    """Создание дублирующейся записи цены."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.rollback = AsyncMock()

    price_in = PriceTSCreate(
        product_id=100,
        dt=date.today(),
        price_sale=1000.0
    )

    mocker.patch(
        "src.services.SalesService.PriceRepo.create_price_record",
        side_effect=IntegrityError("", None, MagicMock())
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await create_price_ts(price_in, mock_session)

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_get_stock_history_success(mocker):
    """Успешное получение истории остатков."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_stock = MagicMock()
    mock_stock.product_id = 100
    mock_stock.quantity = 50
    mock_stock.dt = date.today()
    mock_stock.id = 1

    mocker.patch(
        "src.services.SalesService.StockRepo.read_stocks_history",
        return_value=[mock_stock]
    )

    # Act
    result = await get_stock_history(100, mock_session, limit=10)

    # Assert
    assert len(result) == 1
    assert result[0].product_id == 100


@pytest.mark.asyncio
async def test_get_stock_history_empty(mocker):
    """Получение пустой истории остатков."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mocker.patch(
        "src.services.SalesService.StockRepo.read_stocks_history",
        return_value=[]
    )

    # Act
    result = await get_stock_history(999, mock_session, limit=10)

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_sales_history_success(mocker):
    """Успешное получение истории продаж."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_sale = MagicMock()
    mock_sale.product_id = 100
    mock_sale.sales = 5
    mock_sale.dt = date.today()
    mock_sale.id = 1
    mock_sale.confidence = 0.9

    mocker.patch(
        "src.services.SalesService.SalesRepo.read_sales_history",
        return_value=[mock_sale]
    )

    # Act
    result = await get_sales_history(100, mock_session, limit=10)

    # Assert
    assert len(result) == 1
    assert result[0].sales == 5


@pytest.mark.asyncio
async def test_get_prices_history_success(mocker):
    """Успешное получение истории цен."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_price = MagicMock()
    mock_price.product_id = 100
    mock_price.price_sale = 1000.0
    mock_price.dt = date.today()
    mock_price.id = 1
    mock_price.discount_pct = 10

    mocker.patch(
        "src.services.SalesService.PriceRepo.read_prices_history",
        return_value=[mock_price]
    )

    # Act
    result = await get_prices_history(100, mock_session, limit=10)

    # Assert
    assert len(result) == 1
    assert result[0].price_sale == 1000.0


# =============================================================================
# create_delivery_ts
# =============================================================================

@pytest.mark.asyncio
async def test_create_delivery_ts_success(mocker):
    """Успешное создание записи доставки."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    delivery_in = DeliveryTSCreate(
        product_id=100,
        dt=date.today(),
        delivery_days=5
    )

    mock_delivery = MagicMock()
    mock_delivery.id = 1
    mock_delivery.product_id = 100
    mock_delivery.delivery_days = 5
    mock_delivery.dt = date.today()

    mocker.patch(
        "src.services.SalesService.DeliveryRepo.create_delivery_record",
        return_value=mock_delivery
    )

    # Act
    result = await create_delivery_ts(delivery_in, mock_session)

    # Assert
    assert result.product_id == 100
    assert result.delivery_days == 5


@pytest.mark.asyncio
async def test_create_delivery_ts_duplicate(mocker):
    """Создание дублирующейся записи доставки."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.rollback = AsyncMock()

    delivery_in = DeliveryTSCreate(
        product_id=100,
        dt=date.today(),
        delivery_days=5
    )

    mocker.patch(
        "src.services.SalesService.DeliveryRepo.create_delivery_record",
        side_effect=IntegrityError("", None, MagicMock())
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await create_delivery_ts(delivery_in, mock_session)

    assert exc_info.value.status_code == 409


# =============================================================================
# create_social_ts
# =============================================================================

@pytest.mark.asyncio
async def test_create_social_ts_success(mocker):
    """Успешное создание записи социальных данных."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    social_in = SocialTSCreate(
        product_id=100,
        dt=date.today(),
        rating=4.5,
        feedbacks=100
    )

    mock_social = MagicMock()
    mock_social.id = 1
    mock_social.product_id = 100
    mock_social.rating = 4.5
    mock_social.feedbacks = 100
    mock_social.dt = date.today()

    mocker.patch(
        "src.services.SalesService.SocialRepo.create_social_record",
        return_value=mock_social
    )

    # Act
    result = await create_social_ts(social_in, mock_session)

    # Assert
    assert result.product_id == 100
    assert result.rating == 4.5


@pytest.mark.asyncio
async def test_create_social_ts_duplicate(mocker):
    """Создание дублирующейся записи социальных данных."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.rollback = AsyncMock()

    social_in = SocialTSCreate(
        product_id=100,
        dt=date.today(),
        rating=4.5,
        feedbacks=100
    )

    mocker.patch(
        "src.services.SalesService.SocialRepo.create_social_record",
        side_effect=IntegrityError("", None, MagicMock())
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await create_social_ts(social_in, mock_session)

    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail.lower()


# =============================================================================
# create_predicted_ts
# =============================================================================

@pytest.mark.asyncio
async def test_create_predicted_ts_success(mocker):
    """Успешное создание записи прогноза."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    predicted_in = PredictedSalesTSCreate(
        product_id=100,
        dt=date.today(),
        predicted_sales=10.0,
        model_version="v1"
    )

    mock_predicted = MagicMock()
    mock_predicted.id = 1
    mock_predicted.product_id = 100
    mock_predicted.predicted_sales = 10.0
    mock_predicted.model_version = "v1"
    mock_predicted.dt = date.today()

    mocker.patch(
        "src.services.SalesService.PredictedRepo.create_predict_sales_record",
        return_value=mock_predicted
    )

    # Act
    result = await create_predicted_ts(predicted_in, mock_session)

    # Assert
    assert result.product_id == 100
    assert result.predicted_sales == 10.0


@pytest.mark.asyncio
async def test_create_predicted_ts_duplicate(mocker):
    """Создание дублирующейся записи прогноза."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.rollback = AsyncMock()

    predicted_in = PredictedSalesTSCreate(
        product_id=100,
        dt=date.today(),
        predicted_sales=10.0,
        model_version="v1"
    )

    mocker.patch(
        "src.services.SalesService.PredictedRepo.create_predict_sales_record",
        side_effect=IntegrityError("", None, MagicMock())
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await create_predicted_ts(predicted_in, mock_session)

    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail.lower()


# =============================================================================
# get_deliveries_history
# =============================================================================

@pytest.mark.asyncio
async def test_get_deliveries_history_success(mocker):
    """Успешное получение истории доставок."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_delivery = MagicMock()
    mock_delivery.id = 1
    mock_delivery.product_id = 100
    mock_delivery.delivery_days = 5
    mock_delivery.dt = date.today()

    mocker.patch(
        "src.services.SalesService.DeliveryRepo.read_delivery_history",
        return_value=[mock_delivery]
    )

    # Act
    result = await get_deliveries_history(100, mock_session, limit=10)

    # Assert
    assert len(result) == 1
    assert result[0].delivery_days == 5


# =============================================================================
# get_socials_history
# =============================================================================

@pytest.mark.asyncio
async def test_get_socials_history_success(mocker):
    """Успешное получение истории социальных данных."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_social = MagicMock()
    mock_social.id = 1
    mock_social.product_id = 100
    mock_social.rating = 4.5
    mock_social.feedbacks = 100
    mock_social.dt = date.today()

    mocker.patch(
        "src.services.SalesService.SocialRepo.read_socials_history",
        return_value=[mock_social]
    )

    # Act
    result = await get_socials_history(100, mock_session, limit=10)

    # Assert
    assert len(result) == 1
    assert result[0].rating == 4.5


# =============================================================================
# get_predicted_sales_history
# =============================================================================

@pytest.mark.asyncio
async def test_get_predicted_sales_history_success(mocker):
    """Успешное получение истории прогнозов."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_predicted = MagicMock()
    mock_predicted.id = 1
    mock_predicted.product_id = 100
    mock_predicted.predicted_sales = 10.0
    mock_predicted.model_version = "v1"
    mock_predicted.dt = date.today()

    mocker.patch(
        "src.services.SalesService.PredictedRepo.read_predict_sales_history",
        return_value=[mock_predicted]
    )

    # Act
    result = await get_predicted_sales_history(100, mock_session, limit=10)

    # Assert
    assert len(result) == 1
    assert result[0].predicted_sales == 10.0


# =============================================================================
# calculate_proxy_sales
# =============================================================================

def test_calculate_proxy_sales_positive(mocker):
    """Расчёт продаж при уменьшении остатков."""
    # Arrange
    stocks_in = [
        StockTSCreate(product_id=1, dt=date.today(), quantity=50),
        StockTSCreate(product_id=2, dt=date.today(), quantity=30),
    ]

    old_stocks_map = {
        1: 60,  # Было 60, стало 50 → продажа 10
        2: 40,  # Было 40, стало 30 → продажа 10
    }

    # Act
    result = calculate_proxy_sales(stocks_in, old_stocks_map, confidence=0.9)

    # Assert
    assert len(result) == 2
    assert result[0].sales == 10
    assert result[0].confidence == 0.9
    assert result[1].sales == 10


def test_calculate_proxy_sales_no_change(mocker):
    """Нет продаж, остатки не изменились."""
    # Arrange
    stocks_in = [
        StockTSCreate(product_id=1, dt=date.today(), quantity=50),
    ]

    old_stocks_map = {1: 50}  # Без изменений

    # Act
    result = calculate_proxy_sales(stocks_in, old_stocks_map)

    # Assert
    assert len(result) == 0


def test_calculate_proxy_sales_increase(mocker):
    """Остатки увеличились (возврат товара)."""
    # Arrange
    stocks_in = [
        StockTSCreate(product_id=1, dt=date.today(), quantity=60),
    ]

    old_stocks_map = {1: 50}  # Стало больше

    # Act
    result = calculate_proxy_sales(stocks_in, old_stocks_map)

    # Assert
    assert len(result) == 0  # Нет продаж


def test_calculate_proxy_sales_missing_product(mocker):
    """Продукт отсутствует в old_stocks_map."""
    # Arrange
    stocks_in = [
        StockTSCreate(product_id=999, dt=date.today(), quantity=50),
    ]

    old_stocks_map = {1: 60, 2: 40}  # Нет product_id=999

    # Act
    result = calculate_proxy_sales(stocks_in, old_stocks_map)

    # Assert
    assert len(result) == 0


# =============================================================================
# analytics_data
# =============================================================================

@pytest.mark.asyncio
async def test_analytics_data_empty_stocks(mocker):
    """Пустой список остатков."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    # Act
    result = await analytics_data([], mock_session)

    # Assert
    assert result["status"] == "skipped"
    assert result["detail"] == "Empty stock list"


@pytest.mark.asyncio
async def test_analytics_data_success(mocker):
    """Успешная обработка данных."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    stocks_in = [
        StockTSCreate(product_id=1, dt=date.today(), quantity=50),
    ]

    mock_latest_stock = MagicMock()
    mock_latest_stock.product_id = 1
    mock_latest_stock.quantity = 60

    mocker.patch(
        "src.services.SalesService.StockRepo.read_latest_stocks_for_products",
        return_value=[mock_latest_stock]
    )
    mocker.patch(
        "src.services.SalesService.SalesRepo.create_sales_bulk",
        return_value=[MagicMock()]
    )
    mocker.patch(
        "src.services.SalesService.StockRepo.create_stocks_bulk",
        return_value=[MagicMock()]
    )

    # Act
    result = await analytics_data(stocks_in, mock_session)

    # Assert
    assert result["status"] == "success"
    assert "stocks_processed" in result
    assert "sales_detected" in result


@pytest.mark.asyncio
async def test_analytics_data_integrity_error(mocker):
    """IntegrityError при сохранении."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.rollback = AsyncMock()

    stocks_in = [
        StockTSCreate(product_id=1, dt=date.today(), quantity=50),
    ]

    mocker.patch(
        "src.services.SalesService.StockRepo.read_latest_stocks_for_products",
        return_value=[]
    )
    mocker.patch(
        "src.services.SalesService.StockRepo.create_stocks_bulk",
        side_effect=IntegrityError("", None, MagicMock())
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await analytics_data(stocks_in, mock_session)

    assert exc_info.value.status_code == 409
    assert "Data conflict" in exc_info.value.detail


# =============================================================================
# get_product_analytics
# =============================================================================

@pytest.mark.asyncio
async def test_get_product_analytics_success(mocker):
    """Успешная аналитика товара."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_stock = MagicMock()
    mock_stock.quantity = 100

    mocker.patch(
        "src.services.SalesService.SalesRepo.calculate_velocity_with_oos",
        return_value=10.0  # 10 продаж в день
    )
    mocker.patch(
        "src.services.SalesService.StockRepo.read_stock_latest",
        return_value=mock_stock
    )

    # Act
    result = await get_product_analytics(1, mock_session)

    # Assert
    assert result["velocity"] == 10.0
    assert result["current_stock"] == 100
    assert result["days_to_oos"] == 10  # 100 / 10


@pytest.mark.asyncio
async def test_get_product_analytics_no_stock(mocker):
    """Товар отсутствует (нет остатков)."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mocker.patch(
        "src.services.SalesService.SalesRepo.calculate_velocity_with_oos",
        return_value=5.0
    )
    mocker.patch(
        "src.services.SalesService.StockRepo.read_stock_latest",
        return_value=None
    )

    # Act
    result = await get_product_analytics(1, mock_session)

    # Assert
    assert result["current_stock"] == 0
    assert result["days_to_oos"] == 0  # 0 / 5 = 0


@pytest.mark.asyncio
async def test_get_product_analytics_zero_velocity(mocker):
    """Нулевая скорость продаж."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_stock = MagicMock()
    mock_stock.quantity = 100

    mocker.patch(
        "src.services.SalesService.SalesRepo.calculate_velocity_with_oos",
        return_value=0.0
    )
    mocker.patch(
        "src.services.SalesService.StockRepo.read_stock_latest",
        return_value=mock_stock
    )

    # Act
    result = await get_product_analytics(1, mock_session)

    # Assert
    assert result["days_to_oos"] == 999  # default при нулевой скорости


# =============================================================================
# process_full
# =============================================================================

@pytest.mark.asyncio
async def test_process_full_success(mocker):
    """Успешная обработка полного пакета данных."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    mock_analytics = mocker.patch(
        "src.services.SalesService.analytics_data",
        return_value={"stocks_processed": 1, "sales_detected": 0}
    )
    mocker.patch(
        "src.services.SalesService.PriceRepo.create_prices_bulk",
        return_value=None
    )
    mocker.patch(
        "src.services.SalesService.DeliveryRepo.create_deliveries_bulk",
        return_value=None
    )
    mocker.patch(
        "src.services.SalesService.SocialRepo.create_socials_bulk",
        return_value=None
    )
    mocker.patch(
        "src.services.SalesService.ProductRepo.bulk_update_products",
        return_value=None
    )

    from datetime import date
    mock_data_pack = FullPayload(
        products_update=[],
        stocks=[MagicMock(dt=date.today())],
        prices=[MagicMock(dt=date.today())],
        deliveries=[MagicMock(dt=date.today())],
        socials=[MagicMock(dt=date.today())]
    )

    # Act
    result = await process_full(mock_data_pack, mock_session)

    # Assert
    assert result["status"] == "success"
    assert result["metadata_updated"] == 0  # products_update пуст
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_process_full_no_products_update(mocker):
    """Обработка без обновления товаров."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    mocker.patch(
        "src.services.SalesService.analytics_data",
        return_value={"stocks_processed": 1, "sales_detected": 0}
    )
    mocker.patch(
        "src.services.SalesService.PriceRepo.create_prices_bulk",
        return_value=None
    )
    mocker.patch(
        "src.services.SalesService.DeliveryRepo.create_deliveries_bulk",
        return_value=None
    )
    mocker.patch(
        "src.services.SalesService.SocialRepo.create_socials_bulk",
        return_value=None
    )

    from datetime import date
    mock_data_pack = FullPayload(
        products_update=None,
        stocks=[MagicMock(dt=date.today())],
        prices=[],
        deliveries=[],
        socials=[]
    )

    # Act
    result = await process_full(mock_data_pack, mock_session)

    # Assert
    assert result["metadata_updated"] == 0


@pytest.mark.asyncio
async def test_process_full_error_rollback(mocker):
    """Откат при ошибке."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.rollback = AsyncMock()

    from datetime import date
    from src.db.schemas.Product import ProductUpdate

    mock_product_update = ProductUpdate(name="Test")

    mocker.patch(
        "src.services.SalesService.ProductRepo.bulk_update_products",
        side_effect=Exception("DB Error")
    )

    mock_data_pack = FullPayload(
        products_update=[mock_product_update],
        stocks=[],
        prices=[],
        deliveries=[],
        socials=[]
    )

    # Act & Assert - Exception пробрасывается вверх
    with pytest.raises(Exception):
        await process_full(mock_data_pack, mock_session)

    mock_session.rollback.assert_called_once()
