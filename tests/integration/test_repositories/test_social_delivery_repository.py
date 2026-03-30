"""
Интеграционные тесты для SocialTSRepositories и DeliveryTSRepositories.

Тестируемые методы SocialTSRepositories:
- create_social_record
- create_socials_bulk
- read_social_latest
- read_socials_history
- delete_social_by_date

Тестируемые методы DeliveryTSRepositories:
- create_delivery_record
- create_deliveries_bulk
- read_latest_delivery
- read_delivery_history
- delete_delivery_by_date
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.db.models.Product import Product
from src.db.models.SocialTS import SocialTS
from src.db.models.DeliveryTS import DeliveryTS
from src.db.schemas.SocialTS import SocialTSCreate
from src.db.schemas.DeliveryTS import DeliveryTSCreate
from src.db.repositories.SocialTSRepositories import (
    create_social_record,
    create_socials_bulk,
    read_social_latest,
    read_socials_history,
    delete_social_by_date,
)
from src.db.repositories.DeliveryTSRepositories import (
    create_delivery_record,
    create_deliveries_bulk,
    read_latest_delivery,
    read_delivery_history,
    delete_delivery_by_date,
)


@pytest.fixture
async def test_product(db_session: AsyncSession):
    """Фикстура: тестовый товар."""
    product = Product(
        product_id=12000,
        name="Social/Delivery Test Product",
        brand="TestBrand",
        subject="TestCategory",
        entity="TestEntity"
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
            product_id=13000 + i,
            name=f"Batch Product {i}",
            brand="TestBrand",
            subject="TestCategory",
            entity="TestEntity"
        )
        db_session.add(product)
        products.append(product)
    
    await db_session.commit()
    return products


# =============================================================================
# SocialTSRepositories тесты
# =============================================================================

# -----------------------------------------------------------------------------
# create_social_record тесты
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_social_record(db_session: AsyncSession, test_product):
    """Создание одиночной записи социальных данных."""
    # Arrange
    social_in = SocialTSCreate(
        product_id=test_product.product_id,
        dt=date.today(),
        rating=4.5,
        feedbacks=100
    )

    # Act
    result = await create_social_record(social_in, db_session)
    await db_session.commit()
    await db_session.refresh(result)

    # Assert
    assert result is not None
    assert result.product_id == test_product.product_id
    assert result.rating == 4.5
    assert result.feedbacks == 100


@pytest.mark.asyncio
async def test_create_social_record_multiple_dates(db_session: AsyncSession, test_product):
    """Создание записей социальных данных за разные даты."""
    # Arrange
    records = []
    for i in range(7):
        social_in = SocialTSCreate(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            rating=4.0 + i * 0.1,
            feedbacks=50 + i * 10
        )
        records.append(await create_social_record(social_in, db_session))
    
    await db_session.commit()

    # Assert
    assert len(records) == 7


# -----------------------------------------------------------------------------
# create_socials_bulk тесты
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_socials_bulk(db_session: AsyncSession, test_product):
    """Массовое создание записей социальных данных."""
    # Arrange
    socials_in = [
        SocialTSCreate(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            rating=4.0 + i * 0.05,
            feedbacks=50 + i * 5
        )
        for i in range(14)
    ]

    # Act
    result = await create_socials_bulk(socials_in, db_session)
    await db_session.commit()

    # Assert
    assert len(result) == 14


@pytest.mark.asyncio
async def test_create_socials_bulk_empty(db_session: AsyncSession):
    """Массовое создание с пустым списком."""
    # Act
    result = await create_socials_bulk([], db_session)

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_create_socials_bulk_idempotency(db_session: AsyncSession, test_product):
    """Идемпотентность массового создания."""
    # Arrange
    socials_in = [
        SocialTSCreate(
            product_id=test_product.product_id,
            dt=date.today(),
            rating=4.5,
            feedbacks=100
        )
    ]

    # Создаём первый раз
    first_result = await create_socials_bulk(socials_in, db_session)
    await db_session.commit()
    
    # Пытаемся создать дубликат
    second_result = await create_socials_bulk(socials_in, db_session)
    await db_session.commit()

    # Assert
    assert len(first_result) == 1
    assert len(second_result) == 0  # Дубликат не создан


@pytest.mark.asyncio
async def test_create_socials_bulk_multiple_products(
    db_session: AsyncSession,
    test_products_batch
):
    """Массовое создание записей для нескольких товаров."""
    # Arrange
    socials_in = []
    for product in test_products_batch:
        for i in range(7):
            socials_in.append(
                SocialTSCreate(
                    product_id=product.product_id,
                    dt=date.today() - timedelta(days=i),
                    rating=4.0,
                    feedbacks=50
                )
            )

    # Act
    result = await create_socials_bulk(socials_in, db_session)
    await db_session.commit()

    # Assert
    assert len(result) == len(test_products_batch) * 7


# -----------------------------------------------------------------------------
# read_social_latest тесты
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_read_social_latest(db_session: AsyncSession, test_product):
    """Чтение последней записи социальных данных."""
    # Arrange
    for i in range(5):
        social = SocialTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            rating=4.0 + i * 0.1,
            feedbacks=50 + i * 10
        )
        db_session.add(social)
    await db_session.commit()

    # Act
    result = await read_social_latest(test_product.product_id, db_session)

    # Assert
    assert result is not None
    assert result.dt == date.today()
    assert result.rating == 4.0


@pytest.mark.asyncio
async def test_read_social_latest_not_found(db_session: AsyncSession):
    """Чтение последней записи для несуществующего товара."""
    # Act
    result = await read_social_latest(99999, db_session)

    # Assert
    assert result is None


# -----------------------------------------------------------------------------
# read_socials_history тесты
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_read_socials_history(db_session: AsyncSession, test_product):
    """Чтение истории социальных данных."""
    # Arrange
    for i in range(25):
        social = SocialTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            rating=4.0,
            feedbacks=50 + i
        )
        db_session.add(social)
    await db_session.commit()

    # Act
    result = await read_socials_history(test_product.product_id, db_session, limit=10)

    # Assert
    assert len(result) == 10
    for i in range(len(result) - 1):
        assert result[i].dt >= result[i + 1].dt


@pytest.mark.asyncio
async def test_read_socials_history_empty(db_session: AsyncSession, test_product):
    """Чтение истории при отсутствии данных."""
    # Act
    result = await read_socials_history(test_product.product_id, db_session, limit=10)

    # Assert
    assert len(result) == 0


# -----------------------------------------------------------------------------
# delete_social_by_date тесты
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_social_by_date(db_session: AsyncSession, test_product):
    """Удаление записи социальных данных по дате."""
    # Arrange
    target_date = date.today() - timedelta(days=5)
    for i in range(10):
        social = SocialTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            rating=4.0,
            feedbacks=50
        )
        db_session.add(social)
    await db_session.commit()

    # Act
    await delete_social_by_date(test_product.product_id, target_date, db_session)
    await db_session.commit()

    # Assert
    history = await read_socials_history(test_product.product_id, db_session, limit=100)
    assert all(s.dt != target_date for s in history)


# =============================================================================
# DeliveryTSRepositories тесты
# =============================================================================

# -----------------------------------------------------------------------------
# create_delivery_record тесты
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_delivery_record(db_session: AsyncSession, test_product):
    """Создание одиночной записи данных доставки."""
    # Arrange
    delivery_in = DeliveryTSCreate(
        product_id=test_product.product_id,
        dt=date.today(),
        delivery_days=5
    )

    # Act
    result = await create_delivery_record(delivery_in, db_session)
    await db_session.commit()
    await db_session.refresh(result)

    # Assert
    assert result is not None
    assert result.product_id == test_product.product_id
    assert result.delivery_days == 5


@pytest.mark.asyncio
async def test_create_delivery_record_multiple_dates(db_session: AsyncSession, test_product):
    """Создание записей доставки за разные даты."""
    # Arrange
    records = []
    for i in range(7):
        delivery_in = DeliveryTSCreate(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            delivery_days=3 + i
        )
        records.append(await create_delivery_record(delivery_in, db_session))
    
    await db_session.commit()

    # Assert
    assert len(records) == 7


# -----------------------------------------------------------------------------
# create_deliveries_bulk тесты
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_deliveries_bulk(db_session: AsyncSession, test_product):
    """Массовое создание записей доставки."""
    # Arrange
    deliveries_in = [
        DeliveryTSCreate(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            delivery_days=3 + (i % 5)
        )
        for i in range(14)
    ]

    # Act
    result = await create_deliveries_bulk(deliveries_in, db_session)
    await db_session.commit()

    # Assert
    assert len(result) == 14


@pytest.mark.asyncio
async def test_create_deliveries_bulk_empty(db_session: AsyncSession):
    """Массовое создание с пустым списком."""
    # Act
    result = await create_deliveries_bulk([], db_session)

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_create_deliveries_bulk_idempotency(db_session: AsyncSession, test_product):
    """Идемпотентность массового создания."""
    # Arrange
    deliveries_in = [
        DeliveryTSCreate(
            product_id=test_product.product_id,
            dt=date.today(),
            delivery_days=5
        )
    ]

    # Создаём первый раз
    first_result = await create_deliveries_bulk(deliveries_in, db_session)
    await db_session.commit()
    
    # Пытаемся создать дубликат
    second_result = await create_deliveries_bulk(deliveries_in, db_session)
    await db_session.commit()

    # Assert
    assert len(first_result) == 1
    assert len(second_result) == 0  # Дубликат не создан


@pytest.mark.asyncio
async def test_create_deliveries_bulk_multiple_products(
    db_session: AsyncSession,
    test_products_batch
):
    """Массовое создание записей для нескольких товаров."""
    # Arrange
    deliveries_in = []
    for product in test_products_batch:
        for i in range(7):
            deliveries_in.append(
                DeliveryTSCreate(
                    product_id=product.product_id,
                    dt=date.today() - timedelta(days=i),
                    delivery_days=3 + product.product_id % 3
                )
            )

    # Act
    result = await create_deliveries_bulk(deliveries_in, db_session)
    await db_session.commit()

    # Assert
    assert len(result) == len(test_products_batch) * 7


# -----------------------------------------------------------------------------
# read_latest_delivery тесты
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_read_latest_delivery(db_session: AsyncSession, test_product):
    """Чтение последней записи доставки."""
    # Arrange
    for i in range(5):
        delivery = DeliveryTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            delivery_days=3 + i
        )
        db_session.add(delivery)
    await db_session.commit()

    # Act
    result = await read_latest_delivery(test_product.product_id, db_session)

    # Assert
    assert result is not None
    assert result.dt == date.today()
    assert result.delivery_days == 3


@pytest.mark.asyncio
async def test_read_latest_delivery_not_found(db_session: AsyncSession):
    """Чтение последней записи для несуществующего товара."""
    # Act
    result = await read_latest_delivery(99999, db_session)

    # Assert
    assert result is None


# -----------------------------------------------------------------------------
# read_delivery_history тесты
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_read_delivery_history(db_session: AsyncSession, test_product):
    """Чтение истории доставки."""
    # Arrange
    for i in range(25):
        delivery = DeliveryTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            delivery_days=3 + (i % 7)
        )
        db_session.add(delivery)
    await db_session.commit()

    # Act
    result = await read_delivery_history(test_product.product_id, db_session, limit=10)

    # Assert
    assert len(result) == 10
    for i in range(len(result) - 1):
        assert result[i].dt >= result[i + 1].dt


@pytest.mark.asyncio
async def test_read_delivery_history_empty(db_session: AsyncSession, test_product):
    """Чтение истории при отсутствии данных."""
    # Act
    result = await read_delivery_history(test_product.product_id, db_session, limit=10)

    # Assert
    assert len(result) == 0


# -----------------------------------------------------------------------------
# delete_delivery_by_date тесты
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_delivery_by_date(db_session: AsyncSession, test_product):
    """Удаление записи доставки по дате."""
    # Arrange
    target_date = date.today() - timedelta(days=5)
    for i in range(10):
        delivery = DeliveryTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            delivery_days=3 + i
        )
        db_session.add(delivery)
    await db_session.commit()

    # Act
    await delete_delivery_by_date(test_product.product_id, target_date, db_session)
    await db_session.commit()

    # Assert
    history = await read_delivery_history(test_product.product_id, db_session, limit=100)
    assert all(d.dt != target_date for d in history)
