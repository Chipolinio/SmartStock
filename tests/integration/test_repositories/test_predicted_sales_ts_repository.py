"""
Интеграционные тесты для PredictedSalesTSRepositories.

Тестируемые методы:
- create_predict_sales_record
- create_predict_sales_bulk
- read_latest_prediction
- read_predict_sales_history
- delete_predict_sale_by_date
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.db.models.Product import Product
from src.db.models.PredictedSalesTS import PredictedSalesTS
from src.db.schemas.PredictedSalesTS import PredictedSalesTSCreate
from src.db.repositories.PredictedSalesTSRepositories import (
    create_predict_sales_record,
    create_predict_sales_bulk,
    read_latest_prediction,
    read_predict_sales_history,
    delete_predict_sale_by_date,
)


@pytest.fixture
async def test_product(db_session: AsyncSession):
    """Фикстура: тестовый товар."""
    product = Product(
        product_id=10000,
        name="Predicted Sales Test Product",
        brand="PredictBrand",
        subject="PredictCategory",
        entity="PredictEntity"
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
            product_id=11000 + i,
            name=f"Predict Batch Product {i}",
            brand="PredictBrand",
            subject="PredictCategory",
            entity="PredictEntity"
        )
        db_session.add(product)
        products.append(product)
    
    await db_session.commit()
    return products


# =============================================================================
# create_predict_sales_record тесты
# =============================================================================

@pytest.mark.asyncio
async def test_create_predict_sales_record(db_session: AsyncSession, test_product):
    """Создание одиночной записи прогноза продаж."""
    # Arrange
    predict_in = PredictedSalesTSCreate(
        product_id=test_product.product_id,
        dt=date.today(),
        predicted_sales=25.5,
        model_version="v1.0.0"
    )

    # Act
    result = await create_predict_sales_record(predict_in, db_session)
    await db_session.commit()
    await db_session.refresh(result)

    # Assert
    assert result is not None
    assert result.product_id == test_product.product_id
    assert result.predicted_sales == 25.5
    assert result.model_version == "v1.0.0"


@pytest.mark.asyncio
async def test_create_predict_sales_record_multiple_versions(
    db_session: AsyncSession,
    test_product
):
    """Создание прогнозов разных версий модели."""
    # Arrange
    versions = ["v1.0.0", "v1.1.0", "v2.0.0"]
    records = []
    
    for i, version in enumerate(versions):
        predict_in = PredictedSalesTSCreate(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),  # Разные даты для каждой версии
            predicted_sales=20.0 + float(i),
            model_version=version
        )
        records.append(await create_predict_sales_record(predict_in, db_session))
    
    await db_session.commit()

    # Assert
    assert len(records) == 3
    for record in records:
        assert record.product_id == test_product.product_id


# =============================================================================
# create_predict_sales_bulk тесты
# =============================================================================

@pytest.mark.asyncio
async def test_create_predict_sales_bulk(db_session: AsyncSession, test_product):
    """Массовое создание записей прогнозов."""
    # Arrange
    predicts_in = [
        PredictedSalesTSCreate(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            predicted_sales=20.0 + i * 0.5,
            model_version="v1.0.0"
        )
        for i in range(14)
    ]

    # Act
    result = await create_predict_sales_bulk(predicts_in, db_session)
    await db_session.commit()

    # Assert
    assert len(result) == 14
    for predict in result:
        assert predict.product_id == test_product.product_id


@pytest.mark.asyncio
async def test_create_predict_sales_bulk_empty(db_session: AsyncSession):
    """Массовое создание с пустым списком."""
    # Act
    result = await create_predict_sales_bulk([], db_session)

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_create_predict_sales_bulk_idempotency(db_session: AsyncSession, test_product):
    """Идемпотентность массового создания (дубликаты не создаются)."""
    # Arrange
    predicts_in = [
        PredictedSalesTSCreate(
            product_id=test_product.product_id,
            dt=date.today(),
            predicted_sales=25.0,
            model_version="v1.0.0"
        )
    ]

    # Создаём первый раз
    first_result = await create_predict_sales_bulk(predicts_in, db_session)
    await db_session.commit()
    
    # Пытаемся создать дубликат
    second_result = await create_predict_sales_bulk(predicts_in, db_session)
    await db_session.commit()

    # Assert
    assert len(first_result) == 1
    assert len(second_result) == 0  # Дубликат не создан
    
    # Проверяем что в БД только одна запись
    all_predicts = await read_predict_sales_history(test_product.product_id, db_session, limit=100)
    assert len(all_predicts) == 1


@pytest.mark.asyncio
async def test_create_predict_sales_bulk_multiple_products(
    db_session: AsyncSession,
    test_products_batch
):
    """Массовое создание записей для нескольких товаров."""
    # Arrange
    predicts_in = []
    for product in test_products_batch:
        for i in range(7):
            predicts_in.append(
                PredictedSalesTSCreate(
                    product_id=product.product_id,
                    dt=date.today() - timedelta(days=i),
                    predicted_sales=30.0 + product.product_id * 0.1,
                    model_version="v1.0.0"
                )
            )

    # Act
    result = await create_predict_sales_bulk(predicts_in, db_session)
    await db_session.commit()

    # Assert
    assert len(result) == len(test_products_batch) * 7


# =============================================================================
# read_latest_prediction тесты
# =============================================================================

@pytest.mark.asyncio
async def test_read_latest_prediction(db_session: AsyncSession, test_product):
    """Чтение последнего прогноза."""
    # Arrange
    for i in range(5):
        predict = PredictedSalesTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            predicted_sales=20.0 + i,
            model_version="v1.0.0"
        )
        db_session.add(predict)
    await db_session.commit()

    # Act
    result = await read_latest_prediction(test_product.product_id, db_session)

    # Assert
    assert result is not None
    assert result.dt == date.today()
    assert result.predicted_sales == 20.0


@pytest.mark.asyncio
async def test_read_latest_prediction_not_found(db_session: AsyncSession):
    """Чтение последнего прогноза для несуществующего товара."""
    # Act
    result = await read_latest_prediction(99999, db_session)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_read_latest_prediction_version_not_found(
    db_session: AsyncSession,
    test_product
):
    """Чтение прогноза несуществующей версии модели."""
    # Arrange
    predict = PredictedSalesTS(
        product_id=test_product.product_id,
        dt=date.today(),
        predicted_sales=20.0,
        model_version="v1.0.0"
    )
    db_session.add(predict)
    await db_session.commit()

    # Act
    result = await read_latest_prediction(
        test_product.product_id,
        db_session,
        model_version="v99.0.0"
    )

    # Assert
    assert result is None


# =============================================================================
# read_predict_sales_history тесты
# =============================================================================

@pytest.mark.asyncio
async def test_read_predict_sales_history(db_session: AsyncSession, test_product):
    """Чтение истории прогнозов."""
    # Arrange
    for i in range(25):
        predict = PredictedSalesTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            predicted_sales=15.0 + i * 0.5,
            model_version="v1.0.0"
        )
        db_session.add(predict)
    await db_session.commit()

    # Act
    result = await read_predict_sales_history(test_product.product_id, db_session, limit=10)

    # Assert
    assert len(result) == 10
    # Проверяем сортировку по убыванию даты
    for i in range(len(result) - 1):
        assert result[i].dt >= result[i + 1].dt


@pytest.mark.asyncio
async def test_read_predict_sales_history_empty(db_session: AsyncSession, test_product):
    """Чтение истории при отсутствии данных."""
    # Act
    result = await read_predict_sales_history(test_product.product_id, db_session, limit=10)

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_read_predict_sales_history_limit_zero(db_session: AsyncSession, test_product):
    """Чтение истории с limit=0."""
    # Arrange
    predict = PredictedSalesTS(
        product_id=test_product.product_id,
        dt=date.today(),
        predicted_sales=20.0,
        model_version="v1.0.0"
    )
    db_session.add(predict)
    await db_session.commit()

    # Act
    result = await read_predict_sales_history(test_product.product_id, db_session, limit=0)

    # Assert
    assert len(result) == 0


# =============================================================================
# delete_predict_sale_by_date тесты
# =============================================================================

@pytest.mark.asyncio
async def test_delete_predict_sale_by_date(db_session: AsyncSession, test_product):
    """Удаление записи прогноза по дате."""
    # Arrange
    target_date = date.today() - timedelta(days=5)
    for i in range(10):
        predict = PredictedSalesTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            predicted_sales=20.0 - i,
            model_version="v1.0.0"
        )
        db_session.add(predict)
    await db_session.commit()

    # Act
    await delete_predict_sale_by_date(test_product.product_id, target_date, db_session)
    await db_session.commit()

    # Assert
    history = await read_predict_sales_history(test_product.product_id, db_session, limit=100)
    assert all(p.dt != target_date for p in history)


@pytest.mark.asyncio
async def test_delete_predict_sale_by_date_not_exists(db_session: AsyncSession, test_product):
    """Удаление несуществующей записи."""
    # Arrange
    predict = PredictedSalesTS(
        product_id=test_product.product_id,
        dt=date.today(),
        predicted_sales=20.0,
        model_version="v1.0.0"
    )
    db_session.add(predict)
    await db_session.commit()

    # Act
    await delete_predict_sale_by_date(
        test_product.product_id,
        date.today() - timedelta(days=100),
        db_session
    )
    await db_session.commit()

    # Assert
    history = await read_predict_sales_history(test_product.product_id, db_session, limit=10)
    assert len(history) == 1
