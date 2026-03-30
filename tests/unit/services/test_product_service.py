"""
Юнит-тесты для ProductService (функциональный подход).

Тестируемые функции:
- create_product() — создание товара
- get_product_by_id() — получение товара по ID
- get_product_detailed() — детальная информация
- update_product() — обновление товара
- delete_product() — удаление товара
- add_to_favorites() — добавление в избранное
- seeding_single_product() — сидинг товара
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.services.ProductService import (
    create_product,
    create_products_bulk,
    get_product_by_id,
    get_product_detailed,
    get_products_filter,
    update_product,
    delete_product,
    add_to_favorites,
    add_batch_to_favorites,
    seeding_single_product,
)
from src.db.models.Product import Product
from src.db.schemas.Product import ProductCreate, ProductUpdate


@pytest.mark.asyncio
async def test_create_product_success(mocker):
    """Успешное создание товара."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    product_data = ProductCreate(
        product_id=100,
        name="Test Product",
        brand="Test Brand",
        subject="Electronics",
        entity="Gadget"
    )

    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.product_id = 100
    mock_product.name = "Test Product"
    mock_product.brand = "Test Brand"
    mock_product.subject = "Electronics"
    mock_product.entity = "Gadget"

    mocker.patch(
        "src.services.ProductService.ProductRepo.create_product",
        return_value=mock_product
    )

    # Act
    result = await create_product(product_data, mock_session)

    # Assert
    assert result.product_id == 100
    assert result.name == "Test Product"
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_product_duplicate(mocker):
    """Создание дублирующегося товара."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock(side_effect=IntegrityError(
        statement="",
        params=None,
        orig=MagicMock()
    ))
    mock_session.rollback = AsyncMock()

    product_data = ProductCreate(
        product_id=100,
        name="Test Product",
        brand="Test Brand"
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await create_product(product_data, mock_session)

    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail
    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_get_product_by_id_success(mocker):
    """Успешное получение товара по ID."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.product_id = 100
    mock_product.name = "Test Product"
    mock_product.brand = "Test Brand"
    mock_product.subject = "Electronics"
    mock_product.entity = "Gadget"

    mocker.patch(
        "src.services.ProductService.ProductRepo.read_product",
        return_value=mock_product
    )

    # Act
    result = await get_product_by_id(1, mock_session)

    # Assert
    assert result.product_id == 100
    assert result.name == "Test Product"


@pytest.mark.asyncio
async def test_get_product_by_id_not_found(mocker):
    """Получение несуществующего товара."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mocker.patch(
        "src.services.ProductService.ProductRepo.read_product",
        return_value=None
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_product_by_id(999, mock_session)

    assert exc_info.value.status_code == 404
    assert "Product not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_product_detailed_success(mocker):
    """Успешное получение детальной информации о товаре."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.product_id = 100
    mock_product.name = "Test Product"
    mock_product.brand = "Test Brand"
    mock_product.subject = "Electronics"
    mock_product.entity = "Gadget"

    mock_stats = {
        "price": 1000.0,
        "stock": 50,
        "avg_daily_sales": 5.0,
        "days_to_oos": 10,
        "rating": 4.8,
        "reviews_count": 100,
        "total_sales": 500,
        "total_revenue": 500000.0
    }

    mocker.patch(
        "src.services.ProductService.ProductRepo.read_product",
        return_value=mock_product
    )
    mocker.patch(
        "src.services.ProductService.ProductRepo.get_product_detailed_stats",
        return_value=mock_stats
    )

    # Act
    result = await get_product_detailed(100, mock_session)

    # Assert
    assert result.product_id == 100
    assert result.price == 1000.0
    assert result.stock == 50
    assert result.rating == 4.8
    assert result.total_sales == 500


@pytest.mark.asyncio
async def test_get_product_detailed_not_found(mocker):
    """Получение детальной информации о несуществующем товаре."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mocker.patch(
        "src.services.ProductService.ProductRepo.read_product",
        return_value=None
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_product_detailed(999, mock_session)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_product_success(mocker):
    """Успешное обновление товара."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    product_update = ProductUpdate(name="Updated Name")

    mock_updated_product = MagicMock()
    mock_updated_product.id = 1
    mock_updated_product.product_id = 100
    mock_updated_product.name = "Updated Name"
    mock_updated_product.brand = "Test Brand"
    mock_updated_product.subject = "Electronics"
    mock_updated_product.entity = "Gadget"

    mocker.patch(
        "src.services.ProductService.ProductRepo.update_product",
        return_value=mock_updated_product
    )

    # Act
    result = await update_product(1, product_update, mock_session)

    # Assert
    assert result.name == "Updated Name"


@pytest.mark.asyncio
async def test_update_product_not_found(mocker):
    """Обновление несуществующего товара."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    product_update = ProductUpdate(name="Updated Name")

    mocker.patch(
        "src.services.ProductService.ProductRepo.update_product",
        return_value=None
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await update_product(999, product_update, mock_session)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_product_success(mocker):
    """Успешное удаление товара."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.product_id = 100
    mock_product.name = "Test Product"
    mock_product.brand = "Test Brand"
    mock_product.subject = "Electronics"
    mock_product.entity = "Gadget"

    mocker.patch(
        "src.services.ProductService.ProductRepo.read_product",
        return_value=mock_product
    )
    mocker.patch(
        "src.services.ProductService.ProductRepo.delete_product",
        return_value=None
    )

    # Act
    result = await delete_product(1, mock_session)

    # Assert
    assert "deleted successfully" in result["detail"]


@pytest.mark.asyncio
async def test_delete_product_not_found(mocker):
    """Удаление несуществующего товара."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mocker.patch(
        "src.services.ProductService.ProductRepo.read_product",
        return_value=None
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await delete_product(999, mock_session)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_add_to_favorites_product_exists(mocker):
    """Добавление существующего товара в избранное."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    mock_product = MagicMock()
    mock_product.id = 100
    mock_product.product_id = 100
    mock_product.name = "Test Product"
    mock_product.brand = "Test Brand"
    mock_product.subject = "Electronics"
    mock_product.entity = "Gadget"

    mock_favorite = MagicMock()
    mock_favorite.user_id = 1
    mock_favorite.product_id = 100

    mocker.patch(
        "src.services.ProductService.ProductRepo.get_by_article",
        return_value=mock_product
    )
    mocker.patch(
        "src.services.ProductService.UserFavoriteRepo.create_user_favorites",
        return_value=mock_favorite
    )

    # Act
    product, is_pending = await add_to_favorites(
        user_id=1,
        wb_article=100,
        session=mock_session
    )

    # Assert
    assert product is not None
    assert product.product_id == 100
    assert is_pending is False
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_add_to_favorites_product_not_in_db(mocker):
    """Добавление товара, которого нет в БД (скрапер)."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mocker.patch(
        "src.services.ProductService.ProductRepo.get_by_article",
        return_value=None
    )

    # Act
    product, is_pending = await add_to_favorites(
        user_id=1,
        wb_article=999,
        session=mock_session
    )

    # Assert
    assert product is None
    assert is_pending is True


@pytest.mark.asyncio
async def test_add_to_favorites_already_in_favorites(mocker):
    """Добавление уже существующего в избранном товара."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_product = MagicMock(spec=Product)
    mock_product.id = 100

    mocker.patch(
        "src.services.ProductService.ProductRepo.get_by_article",
        return_value=mock_product
    )
    mocker.patch(
        "src.services.ProductService.UserFavoriteRepo.create_user_favorites",
        return_value=None
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await add_to_favorites(user_id=1, wb_article=100, session=mock_session)

    assert exc_info.value.status_code == 409
    assert "already in favorites" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_seeding_single_product_success(mocker):
    """Успешный сидинг товара через скрапер."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    mock_scraper = MagicMock()
    mock_data_pack = MagicMock()
    mock_data_pack.products_update = [{"product_id": 100, "name": "Test"}]

    mock_scraper.fetch_data = AsyncMock(return_value=mock_data_pack)

    mocker.patch(
        "src.services.ProductService.WBScraper",
        return_value=mock_scraper
    )
    mocker.patch(
        "src.services.ProductService.SalesServiceModule.process_full",
        return_value=True
    )
    mocker.patch(
        "src.services.ProductService.UserFavoriteRepo.create_user_favorites",
        return_value=MagicMock()
    )

    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.product_id = 100
    mock_product.name = "Test Product"
    mock_product.brand = "Test Brand"
    mock_product.subject = "Electronics"
    mock_product.entity = "Gadget"

    mocker.patch(
        "src.services.ProductService.ProductRepo.get_by_article",
        return_value=mock_product
    )

    # Act
    result = await seeding_single_product(
        wb_article=100,
        user_id=1,
        session=mock_session
    )

    # Assert
    assert result.product_id == 100
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_seeding_single_product_scraper_error(mocker):
    """Сидинг с ошибкой скрапера (товар не найден на WB)."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_scraper = MagicMock()
    mock_data_pack = MagicMock()
    mock_data_pack.products_update = None

    mock_scraper.fetch_data = AsyncMock(return_value=mock_data_pack)

    mocker.patch(
        "src.services.ProductService.WBScraper",
        return_value=mock_scraper
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await seeding_single_product(wb_article=999, user_id=1, session=mock_session)

    assert exc_info.value.status_code == 404
    assert "not found on Wildberries" in exc_info.value.detail


# =============================================================================
# create_products_bulk
# =============================================================================

@pytest.mark.asyncio
async def test_create_products_bulk_success(mocker):
    """Успешное массовое создание товаров."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    products_data = [
        ProductCreate(product_id=100, name="Product 1", brand="Brand 1", subject="Cat 1", entity="product"),
        ProductCreate(product_id=200, name="Product 2", brand="Brand 2", subject="Cat 2", entity="product"),
    ]

    mock_product1 = MagicMock()
    mock_product1.id = 1
    mock_product1.product_id = 100
    mock_product1.name = "Product 1"
    mock_product1.brand = "Brand 1"
    mock_product1.subject = "Cat 1"
    mock_product1.entity = "product"

    mock_product2 = MagicMock()
    mock_product2.id = 2
    mock_product2.product_id = 200
    mock_product2.name = "Product 2"
    mock_product2.brand = "Brand 2"
    mock_product2.subject = "Cat 2"
    mock_product2.entity = "product"

    mocker.patch(
        "src.services.ProductService.ProductRepo.bulk_upsert_products",
        return_value=[mock_product1, mock_product2]
    )

    # Act
    result = await create_products_bulk(products_data, mock_session)

    # Assert
    assert len(result) == 2
    assert result[0].product_id == 100
    assert result[1].product_id == 200
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_products_bulk_integrity_error(mocker):
    """Массовое создание с ошибкой IntegrityError."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.rollback = AsyncMock()

    products_data = [
        ProductCreate(product_id=100, name="Product 1", brand="Brand 1", subject="Cat 1", entity="product")
    ]

    mocker.patch(
        "src.services.ProductService.ProductRepo.bulk_upsert_products",
        side_effect=IntegrityError("", None, MagicMock())
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await create_products_bulk(products_data, mock_session)

    assert exc_info.value.status_code == 409
    assert "already exist" in exc_info.value.detail
    mock_session.rollback.assert_called_once()


# =============================================================================
# get_products_filter
# =============================================================================

@pytest.mark.asyncio
async def test_get_products_filter_no_filters(mocker):
    """Получение товаров без фильтров."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.product_id = 100
    mock_product.name = "Product 1"
    mock_product.brand = "Brand 1"
    mock_product.subject = "Cat 1"
    mock_product.entity = "product"

    mocker.patch(
        "src.services.ProductService.ProductRepo.read_products",
        return_value=[mock_product]
    )

    # Act
    result = await get_products_filter(mock_session, skip=0, limit=100)

    # Assert
    assert len(result) == 1
    assert result[0].product_id == 100


@pytest.mark.asyncio
async def test_get_products_filter_with_name(mocker):
    """Фильтрация по имени."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_read = mocker.patch(
        "src.services.ProductService.ProductRepo.read_products",
        return_value=[]
    )

    # Act
    await get_products_filter(mock_session, skip=0, limit=100, name="iPhone")

    # Assert
    mock_read.assert_called_once()
    assert mock_read.call_args.kwargs["name"] == "iPhone"


@pytest.mark.asyncio
async def test_get_products_filter_with_brand(mocker):
    """Фильтрация по бренду."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_read = mocker.patch(
        "src.services.ProductService.ProductRepo.read_products",
        return_value=[]
    )

    # Act
    await get_products_filter(mock_session, skip=0, limit=100, brand="Apple")

    # Assert
    mock_read.assert_called_once()
    assert mock_read.call_args.kwargs["brand"] == "Apple"


@pytest.mark.asyncio
async def test_get_products_filter_with_subject(mocker):
    """Фильтрация по категории."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_read = mocker.patch(
        "src.services.ProductService.ProductRepo.read_products",
        return_value=[]
    )

    # Act
    await get_products_filter(mock_session, skip=0, limit=100, subject="Electronics")

    # Assert
    mock_read.assert_called_once()
    assert mock_read.call_args.kwargs["subject"] == "Electronics"


@pytest.mark.asyncio
async def test_get_products_filter_with_entity(mocker):
    """Фильтрация по entity."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_read = mocker.patch(
        "src.services.ProductService.ProductRepo.read_products",
        return_value=[]
    )

    # Act
    await get_products_filter(mock_session, skip=0, limit=100, entity="product")

    # Assert
    mock_read.assert_called_once()
    assert mock_read.call_args.kwargs["entity"] == "product"


@pytest.mark.asyncio
async def test_get_products_filter_pagination(mocker):
    """Пагинация результатов."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_products = []
    for i in range(1, 51):
        mock_p = MagicMock()
        mock_p.id = i
        mock_p.product_id = i
        mock_p.name = f"Product {i}"
        mock_p.brand = "Brand"
        mock_p.subject = "Cat"
        mock_p.entity = "product"
        mock_products.append(mock_p)

    mock_read = mocker.patch(
        "src.services.ProductService.ProductRepo.read_products",
        return_value=mock_products
    )

    # Act
    result = await get_products_filter(mock_session, skip=0, limit=50)

    # Assert
    assert len(result) == 50
    mock_read.assert_called_once()


# =============================================================================
# add_batch_to_favorites
# =============================================================================

@pytest.mark.asyncio
async def test_add_batch_to_favorites_all_exist(mocker):
    """Массовое добавление, все товары в БД."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    mock_product = MagicMock()
    mock_product.id = 100
    mock_product.product_id = 100

    mock_favorite = MagicMock()
    mock_favorite.user_id = 1
    mock_favorite.product_id = 100

    mocker.patch(
        "src.services.ProductService.ProductRepo.get_by_article",
        return_value=mock_product
    )
    mocker.patch(
        "src.services.ProductService.UserFavoriteRepo.create_user_favorites",
        return_value=mock_favorite
    )

    # Act
    result = await add_batch_to_favorites(user_id=1, wb_articles=[100, 200, 300], session=mock_session)

    # Assert
    assert len(result["added"]) == 3
    assert len(result["pending"]) == 0
    assert len(result["already_in_favorites"]) == 0


@pytest.mark.asyncio
async def test_add_batch_to_favorites_some_missing(mocker):
    """Массовое добавление, некоторые товары отсутствуют."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    mock_product = MagicMock()
    mock_product.id = 100
    mock_product.product_id = 100
    mock_product.name = "Product 100"
    mock_product.brand = "Brand"
    mock_product.subject = "Cat"
    mock_product.entity = "product"

    mock_favorite = MagicMock()
    mock_favorite.user_id = 1
    mock_favorite.product_id = 100

    # Первый товар есть, второго нет
    call_count = [0]

    async def mock_get_by_article(article, session):
        call_count[0] += 1
        if article == 100:
            return mock_product
        return None

    mock_get = mocker.patch(
        "src.services.ProductService.ProductRepo.get_by_article",
        side_effect=mock_get_by_article
    )
    mocker.patch(
        "src.services.ProductService.UserFavoriteRepo.create_user_favorites",
        return_value=mock_favorite
    )
    mocker.patch(
        "src.services.Seeder.seed_articles_batch",
        return_value=None
    )

    # Act
    result = await add_batch_to_favorites(user_id=1, wb_articles=[100, 200], session=mock_session)

    # Assert
    assert 100 in result["added"]  # Существующий товар
    assert 200 in result["pending"]  # Отсутствующий товар
    mock_get.assert_called()


@pytest.mark.asyncio
async def test_add_batch_to_favorites_already_in_favorites(mocker):
    """Массовое добавление, некоторые уже в избранном."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    mock_product = MagicMock()
    mock_product.id = 100
    mock_product.product_id = 100

    mocker.patch(
        "src.services.ProductService.ProductRepo.get_by_article",
        return_value=mock_product
    )
    # Возвращаем None (уже в избранном)
    mocker.patch(
        "src.services.ProductService.UserFavoriteRepo.create_user_favorites",
        return_value=None
    )

    # Act
    result = await add_batch_to_favorites(user_id=1, wb_articles=[100, 200], session=mock_session)

    # Assert
    assert len(result["already_in_favorites"]) == 2


@pytest.mark.asyncio
async def test_add_batch_to_favorites_creates_stubs(mocker):
    """Массовое добавление создаёт заглушки."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()

    mock_favorite = MagicMock()
    mock_favorite.user_id = 1
    mock_favorite.product_id = 100

    mock_get = mocker.patch(
        "src.services.ProductService.ProductRepo.get_by_article",
        return_value=None  # Все товары отсутствуют
    )
    mocker.patch(
        "src.services.ProductService.UserFavoriteRepo.create_user_favorites",
        return_value=mock_favorite
    )
    mock_seed = mocker.patch(
        "src.services.Seeder.seed_articles_batch",
        return_value=None
    )

    # Act
    await add_batch_to_favorites(user_id=1, wb_articles=[100, 200, 300], session=mock_session)

    # Assert
    mock_seed.assert_called_once_with([100, 200, 300], mock_session)
    mock_get.assert_called()
