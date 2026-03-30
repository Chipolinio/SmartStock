"""
Юнит-тесты для Seeder (функциональный подход).

Тестируемые функции:
- clean_text_for_api() — очистка текста
- transform_products() — трансформация данных WB
- seed_to_db() — сохранение в БД
- seed_single_article() — сидинг одного товара
- seed_articles_batch() — массовый сидинг
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession


# =============================================================================
# clean_text_for_api
# =============================================================================

def test_clean_text_for_api_removes_special_chars():
    """Очистка от запрещённых символов."""
    from src.services.Seeder import clean_text_for_api

    assert clean_text_for_api("Кеды (синие) !!!") == "Кеды (синие)"
    assert clean_text_for_api("Товар №1") == "Товар №1"
    # @ и # удаляются, но пробел остаётся
    assert clean_text_for_api("Смартфон @Apple #iPhone") == "Смартфон Apple iPhone"


def test_clean_text_for_api_empty_values():
    """Обработка пустых значений."""
    from src.services.Seeder import clean_text_for_api

    assert clean_text_for_api("") == "Unknown"
    assert clean_text_for_api(None) == "Unknown"
    # Пустые пробелы возвращают пустую строку после strip()
    assert clean_text_for_api("  ") == ""


def test_clean_text_for_api_preserves_valid_chars():
    """Сохранение допустимых символов."""
    from src.services.Seeder import clean_text_for_api

    # % удаляется (не в разрешённых символах)
    assert clean_text_for_api("Кофе 100% арабика") == "Кофе 100 арабика"
    assert clean_text_for_api("Чашка 0.5л") == "Чашка 0.5л"
    assert clean_text_for_api("Набор (10 шт.)") == "Набор (10 шт.)"
    assert clean_text_for_api("Кабель USB-C / Lightning") == "Кабель USB-C / Lightning"


def test_clean_text_for_api_trimming():
    """Обрезка пробелов."""
    from src.services.Seeder import clean_text_for_api

    assert clean_text_for_api("  Смартфон  ") == "Смартфон"
    assert clean_text_for_api("\tНаушники\n") == "Наушники"


# =============================================================================
# transform_products
# =============================================================================

def test_transform_products_success():
    """Трансформация сырых данных WB."""
    from src.services.Seeder import transform_products

    raw_products = [
        {
            "id": 100,
            "name": " Смартфон X ",
            "brand": "Brand Y",
            "subjectName": "Electronics",
        }
    ]

    result = transform_products(raw_products)

    assert len(result) == 1
    assert result[0]["product_id"] == 100
    assert result[0]["name"] == "Смартфон X"
    assert result[0]["brand"] == "Brand Y"
    assert result[0]["subject"] == "Electronics"
    assert result[0]["entity"] == "product"


def test_transform_products_multiple_items():
    """Трансформация нескольких товаров."""
    from src.services.Seeder import transform_products

    raw_products = [
        {"id": 1, "name": "Товар 1", "brand": "Brand 1", "subjectName": "Cat 1"},
        {"id": 2, "name": "Товар 2", "brand": "Brand 2", "subjectName": "Cat 2"},
        {"id": 3, "name": "Товар 3", "brand": "Brand 3", "subjectName": "Cat 3"},
    ]

    result = transform_products(raw_products)

    assert len(result) == 3
    assert result[0]["product_id"] == 1
    assert result[1]["product_id"] == 2
    assert result[2]["product_id"] == 3


def test_transform_products_short_name_fix():
    """Исправление короткого имени."""
    from src.services.Seeder import transform_products

    raw_products = [
        {"id": 100, "name": "X", "brand": "B", "subjectName": "Cat"}
    ]

    result = transform_products(raw_products)

    assert result[0]["name"] == "X Item"  # Добавлено " Item"


def test_transform_products_empty_brand_fix():
    """Исправление пустого бренда."""
    from src.services.Seeder import transform_products

    raw_products = [
        {"id": 100, "name": "Товар", "brand": "", "subjectName": "Cat"}
    ]

    result = transform_products(raw_products)

    assert result[0]["brand"] == "Unknown"  # "Unknown" вместо "Generic"


def test_transform_products_truncation():
    """Обрезка длинных значений."""
    from src.services.Seeder import transform_products

    raw_products = [
        {
            "id": 100,
            "name": "A" * 300,  # Длинное имя
            "brand": "B" * 100,  # Длинный бренд
            "subjectName": "Category"
        }
    ]

    result = transform_products(raw_products)

    assert len(result[0]["name"]) <= 200
    assert len(result[0]["brand"]) <= 50


def test_transform_products_default_subject():
    """Subject по умолчанию."""
    from src.services.Seeder import transform_products

    raw_products = [
        {"id": 100, "name": "Товар", "brand": "Brand"}  # Нет subjectName
    ]

    result = transform_products(raw_products)

    assert result[0]["subject"] == "General"


def test_transform_products_empty_list():
    """Пустой список товаров."""
    from src.services.Seeder import transform_products

    result = transform_products([])

    assert result == []


# =============================================================================
# seed_to_db
# =============================================================================

@pytest.mark.asyncio
async def test_seed_to_db_success(mocker):
    """Успешное сохранение товаров в БД."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    products_data = [
        {"product_id": 100, "name": "Товар 1", "brand": "Brand 1", "subject": "Cat 1", "entity": "product"},
        {"product_id": 200, "name": "Товар 2", "brand": "Brand 2", "subject": "Cat 2", "entity": "product"},
    ]

    mock_saved_product1 = MagicMock()
    mock_saved_product1.product_id = 100
    mock_saved_product1.name = "Товар 1"

    mock_saved_product2 = MagicMock()
    mock_saved_product2.product_id = 200
    mock_saved_product2.name = "Товар 2"

    mocker.patch(
        "src.services.Seeder.bulk_upsert_products",
        return_value=[mock_saved_product1, mock_saved_product2]
    )

    # Act
    from src.services.Seeder import seed_to_db
    result = await seed_to_db(products_data, mock_session)

    # Assert
    assert len(result) == 2
    assert result[0].product_id == 100
    assert result[1].product_id == 200
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_seed_to_db_empty_list(mocker):
    """Сохранение пустого списка."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_print = mocker.patch("builtins.print")

    # Act
    from src.services.Seeder import seed_to_db
    result = await seed_to_db([], mock_session)

    # Assert
    assert result == []
    mock_print.assert_called_with("⚠ Нечего отправлять в базу.")


@pytest.mark.asyncio
async def test_seed_to_db_duplicates_removed(mocker):
    """Удаление дубликатов по product_id."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    products_data = [
        {"product_id": 100, "name": "Товар 1", "brand": "Brand 1", "subject": "Cat 1", "entity": "product"},
        {"product_id": 100, "name": "Товар 1 Duplicate", "brand": "Brand 1", "subject": "Cat 1", "entity": "product"},
    ]

    mock_saved_product = MagicMock()
    mock_saved_product.product_id = 100

    mocker.patch(
        "src.services.Seeder.bulk_upsert_products",
        return_value=[mock_saved_product]
    )

    # Act
    from src.services.Seeder import seed_to_db
    result = await seed_to_db(products_data, mock_session)

    # Assert
    assert len(result) == 1  # Дубликат удалён


@pytest.mark.asyncio
async def test_seed_to_db_rollback_on_error(mocker):
    """Откат при ошибке."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock(side_effect=Exception("DB Error"))

    products_data = [
        {"product_id": 100, "name": "Товар", "brand": "Brand", "subject": "Cat", "entity": "product"}
    ]

    mocker.patch(
        "src.services.Seeder.bulk_upsert_products",
        side_effect=Exception("DB Error")
    )

    # Act & Assert
    from src.services.Seeder import seed_to_db
    with pytest.raises(Exception):
        await seed_to_db(products_data, mock_session)

    mock_session.rollback.assert_called_once()


# =============================================================================
# seed_single_article
# =============================================================================

@pytest.mark.asyncio
async def test_seed_single_article_success(mocker):
    """Сидинг одного товара по артикулу."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    mock_saved_product = MagicMock()
    mock_saved_product.id = 1
    mock_saved_product.product_id = 12345
    mock_saved_product.name = "Product 12345"
    mock_saved_product.brand = "Unknown"
    mock_saved_product.subject = "General"
    mock_saved_product.entity = "product"

    mock_bulk = mocker.patch(
        "src.services.Seeder.bulk_upsert_products",
        return_value=[mock_saved_product]
    )

    # Act
    from src.services.Seeder import seed_single_article
    result = await seed_single_article(12345, mock_session)

    # Assert
    assert len(result) == 1
    assert result[0].product_id == 12345

    # Проверка, что создана заглушка
    mock_bulk.assert_called_once()
    args, _ = mock_bulk.call_args
    products = args[0]
    assert products[0].product_id == 12345
    assert products[0].name == "Product 12345"
    assert products[0].brand == "Unknown"


# =============================================================================
# seed_articles_batch
# =============================================================================

@pytest.mark.asyncio
async def test_seed_articles_batch_success(mocker):
    """Массовый сидинг товаров."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    mock_saved_product1 = MagicMock()
    mock_saved_product1.id = 1
    mock_saved_product1.product_id = 111
    mock_saved_product1.name = "Product 111"
    mock_saved_product1.brand = "Unknown"
    mock_saved_product1.subject = "General"
    mock_saved_product1.entity = "product"

    mock_saved_product2 = MagicMock()
    mock_saved_product2.id = 2
    mock_saved_product2.product_id = 222
    mock_saved_product2.name = "Product 222"
    mock_saved_product2.brand = "Unknown"
    mock_saved_product2.subject = "General"
    mock_saved_product2.entity = "product"

    mock_bulk = mocker.patch(
        "src.services.Seeder.bulk_upsert_products",
        return_value=[mock_saved_product1, mock_saved_product2]
    )

    # Act
    from src.services.Seeder import seed_articles_batch
    result = await seed_articles_batch([111, 222], mock_session)

    # Assert
    assert len(result) == 2

    # Проверка заглушек
    mock_bulk.assert_called_once()
    args, _ = mock_bulk.call_args
    products = args[0]
    assert len(products) == 2
    assert products[0].product_id == 111
    assert products[1].product_id == 222
    assert products[0].name == "Product 111"
    assert products[1].name == "Product 222"


@pytest.mark.asyncio
async def test_seed_articles_batch_empty_list(mocker):
    """Массовый сидинг пустого списка."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_print = mocker.patch("builtins.print")

    # Act
    from src.services.Seeder import seed_articles_batch
    result = await seed_articles_batch([], mock_session)

    # Assert
    assert result == []
    mock_print.assert_called_with("⚠ Нечего отправлять в базу.")


@pytest.mark.asyncio
async def test_seed_articles_batch_large_batch(mocker):
    """Массовый сидинг большого количества товаров."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    articles = list(range(1, 101))  # 100 товаров

    mock_saved_products = [MagicMock(product_id=i) for i in articles]

    mocker.patch(
        "src.services.Seeder.bulk_upsert_products",
        return_value=mock_saved_products
    )

    # Act
    from src.services.Seeder import seed_articles_batch
    result = await seed_articles_batch(articles, mock_session)

    # Assert
    assert len(result) == 100
