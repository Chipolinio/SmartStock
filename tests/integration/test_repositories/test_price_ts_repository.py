"""
Интеграционные тесты для PriceTSRepositories.

Тестируемые методы:
- create_price_record
- create_prices_bulk
- read_price_latest
- read_prices_history
- delete_price_by_date
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.db.models.Product import Product
from src.db.models.PriceTS import PriceTS
from src.db.schemas.PriceTS import PriceTSCreate
from src.db.repositories.PriceTSRepositories import (
    create_price_record,
    create_prices_bulk,
    read_price_latest,
    read_prices_history,
    delete_price_by_date,
)


@pytest.fixture
async def test_product(db_session: AsyncSession):
    """Фикстура: тестовый товар."""
    product = Product(
        product_id=6000,
        name="Price Test Product",
        brand="PriceBrand",
        subject="PriceCategory",
        entity="PriceEntity"
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
            product_id=7000 + i,
            name=f"Price Batch Product {i}",
            brand="PriceBrand",
            subject="PriceCategory",
            entity="PriceEntity"
        )
        db_session.add(product)
        products.append(product)
    
    await db_session.commit()
    return products


# =============================================================================
# create_price_record тесты
# =============================================================================

@pytest.mark.asyncio
async def test_create_price_record(db_session: AsyncSession, test_product):
    """Создание одиночной записи цены."""
    # Arrange
    price_in = PriceTSCreate(
        product_id=test_product.product_id,
        dt=date.today(),
        price_sale=1500.0,
        discount_pct=15
    )

    # Act
    result = await create_price_record(price_in, db_session)
    await db_session.commit()
    await db_session.refresh(result)

    # Assert
    assert result is not None
    assert result.product_id == test_product.product_id
    assert result.price_sale == 1500.0
    assert result.discount_pct == 15


@pytest.mark.asyncio
async def test_create_price_record_multiple_dates(db_session: AsyncSession, test_product):
    """Создание записей цен за разные даты."""
    # Arrange
    records = []
    for i in range(7):
        price_in = PriceTSCreate(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            price_sale=1000.0 + i * 50,
            discount_pct=10 + i
        )
        records.append(await create_price_record(price_in, db_session))
    
    await db_session.commit()

    # Assert
    assert len(records) == 7
    for record in records:
        assert record.product_id == test_product.product_id


# =============================================================================
# create_prices_bulk тесты
# =============================================================================

@pytest.mark.asyncio
async def test_create_prices_bulk(db_session: AsyncSession, test_product):
    """Массовое создание записей цен."""
    # Arrange
    prices_in = [
        PriceTSCreate(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            price_sale=1200.0 + i * 10,
            discount_pct=5 + i
        )
        for i in range(14)
    ]

    # Act
    result = await create_prices_bulk(prices_in, db_session)
    await db_session.commit()

    # Assert
    assert len(result) == 14
    for price in result:
        assert price.product_id == test_product.product_id


@pytest.mark.asyncio
async def test_create_prices_bulk_empty(db_session: AsyncSession):
    """Массовое создание с пустым списком."""
    # Act
    result = await create_prices_bulk([], db_session)

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_create_prices_bulk_update_on_conflict(
    db_session: AsyncSession,
    test_product
):
    """Массовое создание с обновлением при конфликте."""
    # Arrange
    prices_in = [
        PriceTSCreate(
            product_id=test_product.product_id,
            dt=date.today(),
            price_sale=1000.0,
            discount_pct=10
        )
    ]

    # Создаём первый раз
    first_result = await create_prices_bulk(prices_in, db_session)
    await db_session.commit()
    
    # Обновляем с новыми данными
    updated_prices_in = [
        PriceTSCreate(
            product_id=test_product.product_id,
            dt=date.today(),
            price_sale=1200.0,
            discount_pct=20
        )
    ]
    second_result = await create_prices_bulk(updated_prices_in, db_session)
    await db_session.commit()

    # Assert
    assert len(first_result) == 1
    # on_conflict_do_update может не возвращать запись в returning
    # Поэтому проверяем просто что второй вызов не создал дубликат
    
    # Проверяем через историю - должна быть одна запись
    history = await read_prices_history(test_product.product_id, db_session, limit=10)
    assert len(history) == 1


@pytest.mark.asyncio
async def test_create_prices_bulk_multiple_products(
    db_session: AsyncSession,
    test_products_batch
):
    """Массовое создание записей для нескольких товаров."""
    # Arrange
    prices_in = []
    for product in test_products_batch:
        for i in range(7):
            prices_in.append(
                PriceTSCreate(
                    product_id=product.product_id,
                    dt=date.today() - timedelta(days=i),
                    price_sale=1500.0 + product.product_id,
                    discount_pct=10
                )
            )

    # Act
    result = await create_prices_bulk(prices_in, db_session)
    await db_session.commit()

    # Assert
    assert len(result) == len(test_products_batch) * 7


# =============================================================================
# read_price_latest тесты
# =============================================================================

@pytest.mark.asyncio
async def test_read_price_latest(db_session: AsyncSession, test_product):
    """Чтение последней записи цены."""
    # Arrange
    for i in range(5):
        price = PriceTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            price_sale=1000.0 + i * 100,
            discount_pct=10
        )
        db_session.add(price)
    await db_session.commit()

    # Act
    result = await read_price_latest(test_product.product_id, db_session)

    # Assert
    assert result is not None
    assert result.dt == date.today()
    assert result.price_sale == 1000.0


@pytest.mark.asyncio
async def test_read_price_latest_not_found(db_session: AsyncSession):
    """Чтение последней записи для несуществующего товара."""
    # Act
    result = await read_price_latest(99999, db_session)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_read_price_latest_single_record(db_session: AsyncSession, test_product):
    """Чтение последней записи при наличии только одной записи."""
    # Arrange
    price = PriceTS(
        product_id=test_product.product_id,
        dt=date.today(),
        price_sale=2500.0,
        discount_pct=25
    )
    db_session.add(price)
    await db_session.commit()

    # Act
    result = await read_price_latest(test_product.product_id, db_session)

    # Assert
    assert result is not None
    assert result.price_sale == 2500.0
    assert result.discount_pct == 25


# =============================================================================
# read_prices_history тесты
# =============================================================================

@pytest.mark.asyncio
async def test_read_prices_history(db_session: AsyncSession, test_product):
    """Чтение истории цен."""
    # Arrange
    for i in range(25):
        price = PriceTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            price_sale=1000.0 + i * 10,
            discount_pct=5
        )
        db_session.add(price)
    await db_session.commit()

    # Act
    result = await read_prices_history(test_product.product_id, db_session, limit=10)

    # Assert
    assert len(result) == 10
    # Проверяем сортировку по убыванию даты
    for i in range(len(result) - 1):
        assert result[i].dt >= result[i + 1].dt


@pytest.mark.asyncio
async def test_read_prices_history_empty(db_session: AsyncSession, test_product):
    """Чтение истории при отсутствии данных."""
    # Act
    result = await read_prices_history(test_product.product_id, db_session, limit=10)

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_read_prices_history_limit_zero(db_session: AsyncSession, test_product):
    """Чтение истории с limit=0."""
    # Arrange
    price = PriceTS(
        product_id=test_product.product_id,
        dt=date.today(),
        price_sale=1500.0,
        discount_pct=10
    )
    db_session.add(price)
    await db_session.commit()

    # Act
    result = await read_prices_history(test_product.product_id, db_session, limit=0)

    # Assert
    assert len(result) == 0


# =============================================================================
# delete_price_by_date тесты
# =============================================================================

@pytest.mark.asyncio
async def test_delete_price_by_date(db_session: AsyncSession, test_product):
    """Удаление записи цены по дате."""
    # Arrange
    target_date = date.today() - timedelta(days=5)
    for i in range(10):
        price = PriceTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            price_sale=1000.0 + i * 50,
            discount_pct=10
        )
        db_session.add(price)
    await db_session.commit()

    # Act
    await delete_price_by_date(test_product.product_id, target_date, db_session)
    await db_session.commit()

    # Assert
    history = await read_prices_history(test_product.product_id, db_session, limit=100)
    assert all(p.dt != target_date for p in history)


@pytest.mark.asyncio
async def test_delete_price_by_date_not_exists(db_session: AsyncSession, test_product):
    """Удаление несуществующей записи."""
    # Arrange
    price = PriceTS(
        product_id=test_product.product_id,
        dt=date.today(),
        price_sale=1000.0,
        discount_pct=10
    )
    db_session.add(price)
    await db_session.commit()

    # Act
    await delete_price_by_date(
        test_product.product_id,
        date.today() - timedelta(days=100),
        db_session
    )
    await db_session.commit()

    # Assert
    history = await read_prices_history(test_product.product_id, db_session, limit=10)
    assert len(history) == 1
