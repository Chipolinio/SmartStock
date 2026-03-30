"""
Интеграционные тесты для SalesProxyTSRepositories.

Тестируемые методы:
- create_sale_record
- create_sales_bulk
- read_sale_latest
- read_sales_history
- delete_sale_by_date
- calculate_velocity_with_oos
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.db.models.Product import Product
from src.db.models.SalesProxyTS import SalesProxyTS
from src.db.models.StockTS import StockTS
from src.db.schemas.SalesProxyTS import SalesProxyTSCreate
from src.db.repositories.SalesProxyTSRepositories import (
    create_sale_record,
    create_sales_bulk,
    read_sale_latest,
    read_sales_history,
    delete_sale_by_date,
    calculate_velocity_with_oos,
)


@pytest.fixture
async def test_product(db_session: AsyncSession):
    """Фикстура: тестовый товар."""
    product = Product(
        product_id=4000,
        name="Sales Test Product",
        brand="SalesBrand",
        subject="SalesCategory",
        entity="SalesEntity"
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
            product_id=5000 + i,
            name=f"Sales Batch Product {i}",
            brand="SalesBrand",
            subject="SalesCategory",
            entity="SalesEntity"
        )
        db_session.add(product)
        products.append(product)
    
    await db_session.commit()
    return products


# =============================================================================
# create_sale_record тесты
# =============================================================================

@pytest.mark.asyncio
async def test_create_sale_record(db_session: AsyncSession, test_product):
    """Создание одиночной записи продажи."""
    # Arrange
    sale_in = SalesProxyTSCreate(
        product_id=test_product.product_id,
        dt=date.today(),
        sales=50
    )

    # Act
    result = await create_sale_record(sale_in, db_session)
    await db_session.commit()
    await db_session.refresh(result)

    # Assert
    assert result is not None
    assert result.product_id == test_product.product_id
    assert result.sales == 50
    assert result.dt == date.today()


@pytest.mark.asyncio
async def test_create_sale_record_multiple_dates(db_session: AsyncSession, test_product):
    """Создание записей продаж за разные даты."""
    # Arrange
    records = []
    for i in range(7):
        sale_in = SalesProxyTSCreate(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            sales=10 + i * 5
        )
        records.append(await create_sale_record(sale_in, db_session))
    
    await db_session.commit()

    # Assert
    assert len(records) == 7
    for record in records:
        assert record.product_id == test_product.product_id


# =============================================================================
# create_sales_bulk тесты
# =============================================================================

@pytest.mark.asyncio
async def test_create_sales_bulk(db_session: AsyncSession, test_product):
    """Массовое создание записей продаж."""
    # Arrange
    sales_in = [
        SalesProxyTSCreate(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            sales=20 + i * 2
        )
        for i in range(14)
    ]

    # Act
    result = await create_sales_bulk(sales_in, db_session)
    await db_session.commit()

    # Assert
    assert len(result) == 14
    for sale in result:
        assert sale.product_id == test_product.product_id


@pytest.mark.asyncio
async def test_create_sales_bulk_empty(db_session: AsyncSession):
    """Массовое создание с пустым списком."""
    # Act
    result = await create_sales_bulk([], db_session)

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_create_sales_bulk_idempotency(db_session: AsyncSession, test_product):
    """Идемпотентность массового создания (дубликаты не создаются)."""
    # Arrange
    sales_in = [
        SalesProxyTSCreate(
            product_id=test_product.product_id,
            dt=date.today(),
            sales=100
        )
    ]

    # Создаём первый раз
    first_result = await create_sales_bulk(sales_in, db_session)
    await db_session.commit()
    
    # Пытаемся создать дубликат
    second_result = await create_sales_bulk(sales_in, db_session)
    await db_session.commit()

    # Assert
    assert len(first_result) == 1
    assert len(second_result) == 0  # Дубликат не создан
    
    # Проверяем что в БД только одна запись
    all_sales = await read_sales_history(test_product.product_id, db_session, limit=100)
    assert len(all_sales) == 1


@pytest.mark.asyncio
async def test_create_sales_bulk_multiple_products(
    db_session: AsyncSession,
    test_products_batch
):
    """Массовое создание записей для нескольких товаров."""
    # Arrange
    sales_in = []
    for product in test_products_batch:
        for i in range(7):
            sales_in.append(
                SalesProxyTSCreate(
                    product_id=product.product_id,
                    dt=date.today() - timedelta(days=i),
                    sales=30 + product.product_id
                )
            )

    # Act
    result = await create_sales_bulk(sales_in, db_session)
    await db_session.commit()

    # Assert
    assert len(result) == len(test_products_batch) * 7


# =============================================================================
# read_sale_latest тесты
# =============================================================================

@pytest.mark.asyncio
async def test_read_sale_latest(db_session: AsyncSession, test_product):
    """Чтение последней записи продажи."""
    # Arrange
    for i in range(5):
        sale = SalesProxyTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            sales=10 + i * 5
        )
        db_session.add(sale)
    await db_session.commit()

    # Act
    result = await read_sale_latest(test_product.product_id, db_session)

    # Assert
    assert result is not None
    assert result.dt == date.today()
    assert result.sales == 10


@pytest.mark.asyncio
async def test_read_sale_latest_not_found(db_session: AsyncSession):
    """Чтение последней записи для несуществующего товара."""
    # Act
    result = await read_sale_latest(99999, db_session)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_read_sale_latest_single_record(db_session: AsyncSession, test_product):
    """Чтение последней записи при наличии только одной записи."""
    # Arrange
    sale = SalesProxyTS(
        product_id=test_product.product_id,
        dt=date.today(),
        sales=75
    )
    db_session.add(sale)
    await db_session.commit()

    # Act
    result = await read_sale_latest(test_product.product_id, db_session)

    # Assert
    assert result is not None
    assert result.sales == 75


# =============================================================================
# read_sales_history тесты
# =============================================================================

@pytest.mark.asyncio
async def test_read_sales_history(db_session: AsyncSession, test_product):
    """Чтение истории продаж."""
    # Arrange
    for i in range(25):
        sale = SalesProxyTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            sales=15 + i
        )
        db_session.add(sale)
    await db_session.commit()

    # Act
    result = await read_sales_history(test_product.product_id, db_session, limit=10)

    # Assert
    assert len(result) == 10
    # Проверяем сортировку по убыванию даты
    for i in range(len(result) - 1):
        assert result[i].dt >= result[i + 1].dt


@pytest.mark.asyncio
async def test_read_sales_history_empty(db_session: AsyncSession, test_product):
    """Чтение истории при отсутствии данных."""
    # Act
    result = await read_sales_history(test_product.product_id, db_session, limit=10)

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_read_sales_history_limit_zero(db_session: AsyncSession, test_product):
    """Чтение истории с limit=0."""
    # Arrange
    sale = SalesProxyTS(
        product_id=test_product.product_id,
        dt=date.today(),
        sales=100
    )
    db_session.add(sale)
    await db_session.commit()

    # Act
    result = await read_sales_history(test_product.product_id, db_session, limit=0)

    # Assert
    assert len(result) == 0


# =============================================================================
# delete_sale_by_date тесты
# =============================================================================

@pytest.mark.asyncio
async def test_delete_sale_by_date(db_session: AsyncSession, test_product):
    """Удаление записи продажи по дате."""
    # Arrange
    target_date = date.today() - timedelta(days=5)
    for i in range(10):
        sale = SalesProxyTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            sales=20 - i
        )
        db_session.add(sale)
    await db_session.commit()

    # Act
    await delete_sale_by_date(test_product.product_id, target_date, db_session)
    await db_session.commit()

    # Assert
    history = await read_sales_history(test_product.product_id, db_session, limit=100)
    assert all(s.dt != target_date for s in history)


@pytest.mark.asyncio
async def test_delete_sale_by_date_not_exists(db_session: AsyncSession, test_product):
    """Удаление несуществующей записи."""
    # Arrange
    sale = SalesProxyTS(
        product_id=test_product.product_id,
        dt=date.today(),
        sales=100
    )
    db_session.add(sale)
    await db_session.commit()

    # Act
    await delete_sale_by_date(
        test_product.product_id,
        date.today() - timedelta(days=100),
        db_session
    )
    await db_session.commit()

    # Assert
    history = await read_sales_history(test_product.product_id, db_session, limit=10)
    assert len(history) == 1


# =============================================================================
# calculate_velocity_with_oos тесты
# =============================================================================

@pytest.mark.asyncio
async def test_calculate_velocity_with_oos(db_session: AsyncSession, test_product):
    """Расчёт скорости продаж с учётом дней с остатком."""
    # Arrange - создаём данные за 10 дней
    for i in range(10):
        sale = SalesProxyTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            sales=10
        )
        db_session.add(sale)
        
        # Остаток есть только в 5 днях
        if i < 5:
            stock = StockTS(
                product_id=test_product.product_id,
                dt=date.today() - timedelta(days=i),
                quantity=50
            )
            db_session.add(stock)
    
    await db_session.commit()

    # Act
    velocity = await calculate_velocity_with_oos(test_product.product_id, days=10, session=db_session)

    # Assert
    # Функция считает средние продажи в день только по дням с остатком > 0
    # Продажи за 5 дней с остатком: 5 * 10 = 50
    # Дней с остатком: 5
    # velocity = 50 / 5 = 10.0
    assert velocity == 10.0


@pytest.mark.asyncio
async def test_calculate_velocity_with_oos_no_stock(db_session: AsyncSession, test_product):
    """Расчёт скорости продаж без остатков (OOS)."""
    # Arrange
    for i in range(7):
        sale = SalesProxyTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            sales=15
        )
        db_session.add(sale)
        # Нет записей об остатках
    
    await db_session.commit()

    # Act
    velocity = await calculate_velocity_with_oos(test_product.product_id, days=7, session=db_session)

    # Assert
    assert velocity == 0.0  # Нет дней с остатком > 0


@pytest.mark.asyncio
async def test_calculate_velocity_with_oos_empty(db_session: AsyncSession, test_product):
    """Расчёт скорости продаж при отсутствии данных."""
    # Act
    velocity = await calculate_velocity_with_oos(test_product.product_id, days=30, session=db_session)

    # Assert
    assert velocity == 0.0


@pytest.mark.asyncio
async def test_calculate_velocity_with_oos_partial_stock(
    db_session: AsyncSession,
    test_product
):
    """Расчёт скорости продаж с частичными остатками."""
    # Arrange - 14 дней, остатки только 3 дня
    for i in range(14):
        sale = SalesProxyTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            sales=7
        )
        db_session.add(sale)
        
        if i % 5 == 0:  # Остаток каждые 5 дней
            stock = StockTS(
                product_id=test_product.product_id,
                dt=date.today() - timedelta(days=i),
                quantity=30
            )
            db_session.add(stock)
    
    await db_session.commit()

    # Act
    velocity = await calculate_velocity_with_oos(test_product.product_id, days=14, session=db_session)

    # Assert
    # Дней с остатком: 3 (дни 0, 5, 10)
    # Общий объём продаж за эти дни: 7 * 3 = 21
    # velocity = 21 / 3 = 7.0
    assert velocity > 0
