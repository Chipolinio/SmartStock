"""
Интеграционные тесты для StockTSRepositories.

Тестируемые методы:
- create_stock_record
- create_stocks_bulk
- read_stock_latest
- read_stocks_history
- read_latest_stocks_for_products
- delete_stock_by_date
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.db.models.Product import Product
from src.db.models.StockTS import StockTS
from src.db.schemas.StockTS import StockTSCreate
from src.db.repositories.StockTSRepositories import (
    create_stock_record,
    create_stocks_bulk,
    read_stock_latest,
    read_stocks_history,
    read_latest_stocks_for_products,
    delete_stock_by_date,
)


@pytest.fixture
async def test_product(db_session: AsyncSession):
    """Фикстура: тестовый товар."""
    product = Product(
        product_id=2000,
        name="Stock Test Product",
        brand="StockBrand",
        subject="StockCategory",
        entity="StockEntity"
    )
    db_session.add(product)
    await db_session.commit()
    return product


@pytest.fixture
async def test_products_batch(db_session: AsyncSession):
    """Фикстура: набор товаров для тестирования."""
    products = []
    for i in range(5):
        product = Product(
            product_id=3000 + i,
            name=f"Batch Product {i}",
            brand="BatchBrand",
            subject="BatchCategory",
            entity="BatchEntity"
        )
        db_session.add(product)
        products.append(product)
    
    await db_session.commit()
    return products


# =============================================================================
# create_stock_record тесты
# =============================================================================

@pytest.mark.asyncio
async def test_create_stock_record(db_session: AsyncSession, test_product):
    """Создание одиночной записи остатка."""
    # Arrange
    stock_in = StockTSCreate(
        product_id=test_product.product_id,
        dt=date.today(),
        quantity=100
    )

    # Act
    result = await create_stock_record(stock_in, db_session)
    await db_session.commit()
    await db_session.refresh(result)

    # Assert
    assert result is not None
    assert result.product_id == test_product.product_id
    assert result.quantity == 100
    assert result.dt == date.today()


@pytest.mark.asyncio
async def test_create_stock_record_multiple_dates(db_session: AsyncSession, test_product):
    """Создание записей остатка за разные даты."""
    # Arrange
    records = []
    for i in range(5):
        stock_in = StockTSCreate(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            quantity=100 - i * 10
        )
        records.append(await create_stock_record(stock_in, db_session))
    
    await db_session.commit()

    # Assert
    assert len(records) == 5
    for record in records:
        assert record.product_id == test_product.product_id


# =============================================================================
# create_stocks_bulk тесты
# =============================================================================

@pytest.mark.asyncio
async def test_create_stocks_bulk(db_session: AsyncSession, test_product):
    """Массовое создание записей остатков."""
    # Arrange
    stocks_in = [
        StockTSCreate(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            quantity=100 - i * 5
        )
        for i in range(10)
    ]

    # Act
    result = await create_stocks_bulk(stocks_in, db_session)
    await db_session.commit()

    # Assert
    assert len(result) == 10
    for stock in result:
        assert stock.product_id == test_product.product_id


@pytest.mark.asyncio
async def test_create_stocks_bulk_empty(db_session: AsyncSession):
    """Массовое создание с пустым списком."""
    # Act
    result = await create_stocks_bulk([], db_session)

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_create_stocks_bulk_idempotency(db_session: AsyncSession, test_product):
    """Идемпотентность массового создания (дубликаты не создаются)."""
    # Arrange
    stocks_in = [
        StockTSCreate(
            product_id=test_product.product_id,
            dt=date.today(),
            quantity=100
        )
    ]

    # Создаём первый раз
    first_result = await create_stocks_bulk(stocks_in, db_session)
    await db_session.commit()
    
    # Пытаемся создать дубликат
    second_result = await create_stocks_bulk(stocks_in, db_session)
    await db_session.commit()

    # Assert
    assert len(first_result) == 1
    assert len(second_result) == 0  # Дубликат не создан
    
    # Проверяем что в БД только одна запись
    all_stocks = await read_stocks_history(test_product.product_id, db_session, limit=100)
    assert len(all_stocks) == 1


@pytest.mark.asyncio
async def test_create_stocks_bulk_multiple_products(
    db_session: AsyncSession,
    test_products_batch
):
    """Массовое создание записей для нескольких товаров."""
    # Arrange
    stocks_in = []
    for product in test_products_batch:
        for i in range(5):
            stocks_in.append(
                StockTSCreate(
                    product_id=product.product_id,
                    dt=date.today() - timedelta(days=i),
                    quantity=50 + product.product_id
                )
            )

    # Act
    result = await create_stocks_bulk(stocks_in, db_session)
    await db_session.commit()

    # Assert
    assert len(result) == len(test_products_batch) * 5


# =============================================================================
# read_stock_latest тесты
# =============================================================================

@pytest.mark.asyncio
async def test_read_stock_latest(db_session: AsyncSession, test_product):
    """Чтение последней записи остатка."""
    # Arrange
    for i in range(5):
        stock = StockTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            quantity=100 - i * 10
        )
        db_session.add(stock)
    await db_session.commit()

    # Act
    result = await read_stock_latest(test_product.product_id, db_session)

    # Assert
    assert result is not None
    assert result.dt == date.today()
    assert result.quantity == 100


@pytest.mark.asyncio
async def test_read_stock_latest_not_found(db_session: AsyncSession):
    """Чтение последней записи для несуществующего товара."""
    # Act
    result = await read_stock_latest(99999, db_session)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_read_stock_latest_single_record(db_session: AsyncSession, test_product):
    """Чтение последней записи при наличии только одной записи."""
    # Arrange
    stock = StockTS(
        product_id=test_product.product_id,
        dt=date.today(),
        quantity=50
    )
    db_session.add(stock)
    await db_session.commit()

    # Act
    result = await read_stock_latest(test_product.product_id, db_session)

    # Assert
    assert result is not None
    assert result.quantity == 50


# =============================================================================
# read_stocks_history тесты
# =============================================================================

@pytest.mark.asyncio
async def test_read_stocks_history(db_session: AsyncSession, test_product):
    """Чтение истории остатков."""
    # Arrange
    for i in range(20):
        stock = StockTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            quantity=100 - i
        )
        db_session.add(stock)
    await db_session.commit()

    # Act
    result = await read_stocks_history(test_product.product_id, db_session, limit=10)

    # Assert
    assert len(result) == 10
    # Проверяем сортировку по убыванию даты
    for i in range(len(result) - 1):
        assert result[i].dt >= result[i + 1].dt


@pytest.mark.asyncio
async def test_read_stocks_history_empty(db_session: AsyncSession, test_product):
    """Чтение истории при отсутствии данных."""
    # Act
    result = await read_stocks_history(test_product.product_id, db_session, limit=10)

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_read_stocks_history_limit_zero(db_session: AsyncSession, test_product):
    """Чтение истории с limit=0."""
    # Arrange
    stock = StockTS(
        product_id=test_product.product_id,
        dt=date.today(),
        quantity=100
    )
    db_session.add(stock)
    await db_session.commit()

    # Act
    result = await read_stocks_history(test_product.product_id, db_session, limit=0)

    # Assert
    assert len(result) == 0


# =============================================================================
# read_latest_stocks_for_products тесты
# =============================================================================

@pytest.mark.asyncio
async def test_read_latest_stocks_for_products(
    db_session: AsyncSession,
    test_products_batch
):
    """Чтение последних остатков для списка товаров."""
    # Arrange
    for product in test_products_batch:
        # Создаём несколько записей для каждого товара
        for i in range(5):
            stock = StockTS(
                product_id=product.product_id,
                dt=date.today() - timedelta(days=i),
                quantity=50 + product.product_id - i
            )
            db_session.add(stock)
    await db_session.commit()

    # Act
    product_ids = [p.product_id for p in test_products_batch]
    result = await read_latest_stocks_for_products(product_ids, db_session)

    # Assert
    assert len(result) == len(test_products_batch)
    for stock in result:
        assert stock.dt == date.today()


@pytest.mark.asyncio
async def test_read_latest_stocks_for_products_partial(
    db_session: AsyncSession,
    test_products_batch
):
    """Чтение последних остатков для части товаров."""
    # Arrange
    # Создаём данные только для первых 3 товаров
    for product in test_products_batch[:3]:
        stock = StockTS(
            product_id=product.product_id,
            dt=date.today(),
            quantity=100
        )
        db_session.add(stock)
    await db_session.commit()

    # Act
    product_ids = [p.product_id for p in test_products_batch]
    result = await read_latest_stocks_for_products(product_ids, db_session)

    # Assert
    assert len(result) == 3  # Только для тех, у кого есть данные


@pytest.mark.asyncio
async def test_read_latest_stocks_for_products_empty_list(
    db_session: AsyncSession
):
    """Чтение последних остатков для пустого списка товаров."""
    # Act
    result = await read_latest_stocks_for_products([], db_session)

    # Assert
    assert len(result) == 0


# =============================================================================
# delete_stock_by_date тесты
# =============================================================================

@pytest.mark.asyncio
async def test_delete_stock_by_date(db_session: AsyncSession, test_product):
    """Удаление записи остатка по дате."""
    # Arrange
    target_date = date.today() - timedelta(days=5)
    for i in range(10):
        stock = StockTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            quantity=100 - i
        )
        db_session.add(stock)
    await db_session.commit()

    # Act
    await delete_stock_by_date(test_product.product_id, target_date, db_session)
    await db_session.commit()

    # Assert
    history = await read_stocks_history(test_product.product_id, db_session, limit=100)
    assert all(s.dt != target_date for s in history)


@pytest.mark.asyncio
async def test_delete_stock_by_date_not_exists(db_session: AsyncSession, test_product):
    """Удаление несуществующей записи."""
    # Arrange
    stock = StockTS(
        product_id=test_product.product_id,
        dt=date.today(),
        quantity=100
    )
    db_session.add(stock)
    await db_session.commit()

    # Act
    await delete_stock_by_date(
        test_product.product_id,
        date.today() - timedelta(days=100),
        db_session
    )
    await db_session.commit()

    # Assert
    history = await read_stocks_history(test_product.product_id, db_session, limit=10)
    assert len(history) == 1
