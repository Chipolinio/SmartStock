"""
Интеграционные тесты для ProductFeaturesDailyRepositories.

Тестируемые методы:
- create_features_daily_record
- create_features_daily_bulk
- read_features_latest
- read_features_history
- read_features_by_date
- get_aggregated_features_data
- get_all_features_for_train
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.db.models.Product import Product
from src.db.models.ProductFeaturesDaily import ProductFeaturesDaily
from src.db.models.PriceTS import PriceTS
from src.db.models.StockTS import StockTS
from src.db.models.SocialTS import SocialTS
from src.db.models.SalesProxyTS import SalesProxyTS
from src.db.schemas.ProductFeaturesDaily import ProductFeaturesDailyCreate
from src.db.repositories.ProductFeaturesDailyRepositories import (
    create_features_daily_record,
    create_features_daily_bulk,
    read_features_latest,
    read_features_history,
    read_features_by_date,
    get_aggregated_features_data,
    get_all_features_for_train,
)


@pytest.fixture
async def test_product(db_session: AsyncSession):
    """Фикстура: тестовый товар."""
    product = Product(
        product_id=8000,
        name="Features Test Product",
        brand="FeaturesBrand",
        subject="FeaturesCategory",
        entity="FeaturesEntity"
    )
    db_session.add(product)
    await db_session.commit()
    return product


@pytest.fixture
async def test_products_batch(db_session: AsyncSession):
    """Фикстура: набор товаров для тестирования."""
    products = []
    for i in range(3):
        product = Product(
            product_id=9000 + i,
            name=f"Features Batch Product {i}",
            brand="FeaturesBrand",
            subject="FeaturesCategory",
            entity="FeaturesEntity"
        )
        db_session.add(product)
        products.append(product)
    
    await db_session.commit()
    return products


# =============================================================================
# create_features_daily_record тесты
# =============================================================================

@pytest.mark.asyncio
async def test_create_features_daily_record(db_session: AsyncSession, test_product):
    """Создание одиночной записи фичей."""
    # Arrange
    features_in = ProductFeaturesDailyCreate(
        product_id=test_product.product_id,
        dt=date.today(),
        price=1500.0,
        discount_pct=10,
        rating=4.5,
        feedbacks=100,
        avg_sales_7d=15.0,
        avg_sales_14d=12.0,
        stock_left=50,
        days_to_oos=10,
        price_rank_in_category=1,
        rating_rank_in_category=2
    )

    # Act
    result = await create_features_daily_record(features_in, db_session)

    # Assert
    assert result is not None
    assert result.product_id == test_product.product_id
    assert result.price == 1500.0
    assert result.rating == 4.5


# =============================================================================
# create_features_daily_bulk тесты
# =============================================================================

@pytest.mark.asyncio
async def test_create_features_daily_bulk(db_session: AsyncSession, test_product):
    """Массовое создание записей фичей."""
    # Arrange
    features_in = [
        ProductFeaturesDailyCreate(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            price=1000.0 + i * 50,
            discount_pct=10,
            rating=4.0,
            feedbacks=50 + i * 10,
            avg_sales_7d=10.0,
            avg_sales_14d=8.0,
            stock_left=100 - i * 5,
            days_to_oos=20 - i,
            price_rank_in_category=1,
            rating_rank_in_category=1
        )
        for i in range(7)
    ]

    # Act
    await create_features_daily_bulk(features_in, db_session)
    await db_session.commit()

    # Assert
    history = await read_features_history(test_product.product_id, db_session, limit=10)
    assert len(history) == 7


@pytest.mark.asyncio
async def test_create_features_daily_bulk_empty(db_session: AsyncSession):
    """Массовое создание с пустым списком."""
    # Act
    await create_features_daily_bulk([], db_session)

    # Assert - никаких ошибок


@pytest.mark.asyncio
async def test_create_features_daily_bulk_update_on_conflict(
    db_session: AsyncSession,
    test_product
):
    """Массовое создание с обновлением при конфликте."""
    # Arrange
    features_in = [
        ProductFeaturesDailyCreate(
            product_id=test_product.product_id,
            dt=date.today(),
            price=1000.0,
            discount_pct=10,
            rating=4.0,
            feedbacks=50,
            avg_sales_7d=10.0,
            avg_sales_14d=8.0,
            stock_left=100,
            days_to_oos=20,
            price_rank_in_category=1,
            rating_rank_in_category=1
        )
    ]

    # Создаём первый раз
    await create_features_daily_bulk(features_in, db_session)
    await db_session.commit()
    
    # Обновляем с новыми данными
    updated_features_in = [
        ProductFeaturesDailyCreate(
            product_id=test_product.product_id,
            dt=date.today(),
            price=1200.0,
            discount_pct=15,
            rating=4.8,
            feedbacks=80,
            avg_sales_7d=15.0,
            avg_sales_14d=12.0,
            stock_left=80,
            days_to_oos=15,
            price_rank_in_category=2,
            rating_rank_in_category=1
        )
    ]
    await create_features_daily_bulk(updated_features_in, db_session)
    await db_session.commit()

    # Assert - проверяем что данные обновились
    latest = await read_features_latest(test_product.product_id, db_session)
    assert float(latest.price) == 1200.0
    assert latest.discount_pct == 15
    assert float(latest.rating) == 4.8


# =============================================================================
# read_features_latest тесты
# =============================================================================

@pytest.mark.asyncio
async def test_read_features_latest(db_session: AsyncSession, test_product):
    """Чтение последней записи фичей."""
    # Arrange
    for i in range(5):
        features = ProductFeaturesDaily(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            price=1000.0 + i * 100,
            discount_pct=10,
            rating=4.0,
            feedbacks=50,
            avg_sales_7d=10.0,
            avg_sales_14d=8.0,
            stock_left=100,
            days_to_oos=20,
            price_rank_in_category=1,
            rating_rank_in_category=1
        )
        db_session.add(features)
    await db_session.commit()

    # Act
    result = await read_features_latest(test_product.product_id, db_session)

    # Assert
    assert result is not None
    assert result.dt == date.today()
    assert result.price == 1000.0


@pytest.mark.asyncio
async def test_read_features_latest_not_found(db_session: AsyncSession):
    """Чтение последней записи для несуществующего товара."""
    # Act
    result = await read_features_latest(99999, db_session)

    # Assert
    assert result is None


# =============================================================================
# read_features_history тесты
# =============================================================================

@pytest.mark.asyncio
async def test_read_features_history(db_session: AsyncSession, test_product):
    """Чтение истории фичей."""
    # Arrange
    for i in range(20):
        features = ProductFeaturesDaily(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            price=1000.0 + i * 10,
            discount_pct=10,
            rating=4.0,
            feedbacks=50,
            avg_sales_7d=10.0,
            avg_sales_14d=8.0,
            stock_left=100,
            days_to_oos=20,
            price_rank_in_category=1,
            rating_rank_in_category=1
        )
        db_session.add(features)
    await db_session.commit()

    # Act
    result = await read_features_history(test_product.product_id, db_session, limit=10)

    # Assert
    assert len(result) == 10
    # Проверяем сортировку по убыванию даты
    for i in range(len(result) - 1):
        assert result[i].dt >= result[i + 1].dt


@pytest.mark.asyncio
async def test_read_features_history_empty(db_session: AsyncSession, test_product):
    """Чтение истории при отсутствии данных."""
    # Act
    result = await read_features_history(test_product.product_id, db_session, limit=10)

    # Assert
    assert len(result) == 0


# =============================================================================
# read_features_by_date тесты
# =============================================================================

@pytest.mark.asyncio
async def test_read_features_by_date(db_session: AsyncSession, test_product):
    """Чтение фичей по дате."""
    # Arrange
    target_date = date.today() - timedelta(days=5)
    for i in range(10):
        features = ProductFeaturesDaily(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            price=1000.0 + i * 50,
            discount_pct=10,
            rating=4.0,
            feedbacks=50,
            avg_sales_7d=10.0,
            avg_sales_14d=8.0,
            stock_left=100,
            days_to_oos=20,
            price_rank_in_category=1,
            rating_rank_in_category=1
        )
        db_session.add(features)
    await db_session.commit()

    # Act
    result = await read_features_by_date(db_session, target_date)

    # Assert
    assert len(result) == 1
    assert result[0].dt == target_date


@pytest.mark.asyncio
async def test_read_features_by_date_not_found(db_session: AsyncSession, test_product):
    """Чтение фичей по несуществующей дате."""
    # Arrange
    features = ProductFeaturesDaily(
        product_id=test_product.product_id,
        dt=date.today(),
        price=1000.0,
        discount_pct=10,
        rating=4.0,
        feedbacks=50,
        avg_sales_7d=10.0,
        avg_sales_14d=8.0,
        stock_left=100,
        days_to_oos=20,
        price_rank_in_category=1,
        rating_rank_in_category=1
    )
    db_session.add(features)
    await db_session.commit()

    # Act
    result = await read_features_by_date(db_session, date.today() - timedelta(days=100))

    # Assert
    assert len(result) == 0


# =============================================================================
# get_aggregated_features_data тесты
# =============================================================================

@pytest.mark.asyncio
async def test_get_aggregated_features_data(
    db_session: AsyncSession,
    test_products_batch
):
    """Агрегация фичей для ML."""
    # Arrange - создаём данные для всех товаров на целевую дату
    target_date = date.today()
    
    for product in test_products_batch:
        # PriceTS
        price = PriceTS(
            product_id=product.product_id,
            dt=target_date,
            price_sale=1500.0 + product.product_id * 10,
            discount_pct=10
        )
        db_session.add(price)
        
        # StockTS
        stock = StockTS(
            product_id=product.product_id,
            dt=target_date,
            quantity=100 + product.product_id
        )
        db_session.add(stock)
        
        # SocialTS
        social = SocialTS(
            product_id=product.product_id,
            dt=target_date,
            rating=4.0 + (product.product_id % 5) * 0.1,
            feedbacks=50 + product.product_id
        )
        db_session.add(social)
        
        # SalesProxyTS за прошлые дни для расчёта средних продаж
        for i in range(1, 15):
            sale = SalesProxyTS(
                product_id=product.product_id,
                dt=target_date - timedelta(days=i),
                sales=10 + i
            )
            db_session.add(sale)
    
    await db_session.commit()

    # Act
    result = await get_aggregated_features_data(db_session, target_date)

    # Assert
    assert len(result) == len(test_products_batch)
    for row in result:
        assert row.price_sale is not None
        assert row.quantity is not None
        assert row.rating is not None


@pytest.mark.asyncio
async def test_get_aggregated_features_data_empty(db_session: AsyncSession):
    """Агрегация фичей при отсутствии данных."""
    # Act
    result = await get_aggregated_features_data(db_session, date.today())

    # Assert
    assert len(result) == 0


# =============================================================================
# get_all_features_for_train тесты
# =============================================================================

@pytest.mark.asyncio
async def test_get_all_features_for_train(
    db_session: AsyncSession,
    test_product
):
    """Получение данных для обучения модели."""
    # Arrange
    target_date = date.today()
    
    # Создаём фичи
    features = ProductFeaturesDaily(
        product_id=test_product.product_id,
        dt=target_date,
        price=1500.0,
        discount_pct=10,
        rating=4.5,
        feedbacks=100,
        avg_sales_7d=15.0,
        avg_sales_14d=12.0,
        stock_left=50,
        days_to_oos=10,
        price_rank_in_category=1,
        rating_rank_in_category=1
    )
    db_session.add(features)
    
    # Создаём продажи на следующий день (target для обучения)
    sale = SalesProxyTS(
        product_id=test_product.product_id,
        dt=target_date + timedelta(days=1),
        sales=20
    )
    db_session.add(sale)
    
    await db_session.commit()

    # Act
    result = await get_all_features_for_train(db_session)

    # Assert
    assert len(result) >= 1
    found = False
    for row in result:
        if row.ProductFeaturesDaily.product_id == test_product.product_id:
            found = True
            assert row.real_sales_next_day == 20
            break
    assert found, "Найдена запись с нужным product_id"


@pytest.mark.asyncio
async def test_get_all_features_for_train_no_target(db_session: AsyncSession, test_product):
    """Получение данных для обучения без целевых продаж."""
    # Arrange
    target_date = date.today()
    
    features = ProductFeaturesDaily(
        product_id=test_product.product_id,
        dt=target_date,
        price=1500.0,
        discount_pct=10,
        rating=4.5,
        feedbacks=100,
        avg_sales_7d=15.0,
        avg_sales_14d=12.0,
        stock_left=50,
        days_to_oos=10,
        price_rank_in_category=1,
        rating_rank_in_category=1
    )
    db_session.add(features)
    # Нет продаж на следующий день
    
    await db_session.commit()

    # Act
    result = await get_all_features_for_train(db_session)

    # Assert - записи без продаж на следующий день не попадают в результат
    found = False
    for row in result:
        if row.ProductFeaturesDaily.product_id == test_product.product_id:
            found = True
            break
    assert not found, "Запись без целевых продаж не должна быть в результате"
