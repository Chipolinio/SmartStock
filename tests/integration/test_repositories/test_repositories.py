"""
Интеграционные тесты для репозиториев.

Тестируемые репозитории:
- UserRepositories
- ProductRepositories
- UserFavoriteRepositories
- SalesTS repositories
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.db.models.User import User
from src.db.models.Product import Product
from src.db.models.UserFavorite import UserFavorite
from src.db.models.SalesProxyTS import SalesProxyTS
from src.db.models.StockTS import StockTS
from src.db.models.PriceTS import PriceTS

from src.db.repositories.UserRepositories import (
    read_user_by_id,
    read_user_by_email,
    read_user_by_internal_id,
    update_user,
    update_user_tg_id,
    delete_user
)
from src.db.repositories.ProductRepositories import (
    create_product,
    read_product,
    get_by_article,
    read_products,
    update_product,
    delete_product,
    get_product_detailed_stats
)
from src.db.repositories.UserFavoriteRepositories import (
    read_user_favorites,
    create_user_favorites,
    delete_user_favorites,
    check_product_exists,
    read_user_favorites_with_details
)


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Фикстура: тестовый пользователь."""
    user = User(email="repo_test@example.com", password_hash="hashed", role="user")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_product(db_session: AsyncSession):
    """Фикстура: тестовый товар."""
    product = Product(product_id=100, name="Test Product", brand="Test", subject="Test", entity="Test")
    db_session.add(product)
    await db_session.commit()
    return product


# =============================================================================
# UserRepositories тесты
# =============================================================================

@pytest.mark.asyncio
async def test_read_user_by_id(db_session: AsyncSession, test_user):
    """Чтение пользователя по ID."""
    # Arrange - установим user_id (Telegram ID)
    tg_id = 123456789
    test_user.user_id = tg_id
    await db_session.commit()
    
    # Act
    user = await read_user_by_id(tg_id, db_session)

    # Assert
    assert user is not None
    assert user.user_id == tg_id
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_read_user_by_id_not_found(db_session: AsyncSession):
    """Чтение несуществующего пользователя по ID."""
    # Act
    user = await read_user_by_id(99999, db_session)

    # Assert
    assert user is None


@pytest.mark.asyncio
async def test_read_user_by_email(db_session: AsyncSession, test_user):
    """Чтение пользователя по email."""
    # Act
    user = await read_user_by_email(test_user.email, db_session)

    # Assert
    assert user is not None
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_read_user_by_email_not_found(db_session: AsyncSession):
    """Чтение несуществующего пользователя по email."""
    # Act
    user = await read_user_by_email("nonexistent@example.com", db_session)

    # Assert
    assert user is None


@pytest.mark.asyncio
async def test_read_user_by_internal_id(db_session: AsyncSession, test_user):
    """Чтение пользователя по internal_id."""
    # Act
    user = await read_user_by_internal_id(test_user.id, db_session)

    # Assert
    assert user is not None
    assert user.id == test_user.id


@pytest.mark.asyncio
async def test_update_user(db_session: AsyncSession, test_user):
    """Обновление пользователя."""
    # Arrange
    update_data = {"is_pro": True, "is_active": False}

    # Act
    result = await update_user(test_user.id, update_data, db_session)

    # Assert
    assert result is not None
    # Проверяем, что данные обновились
    await db_session.refresh(test_user)
    assert test_user.is_pro is True
    assert test_user.is_active is False


@pytest.mark.asyncio
async def test_update_user_not_found(db_session: AsyncSession):
    """Обновление несуществующего пользователя."""
    # Arrange
    update_data = {"is_pro": True}

    # Act
    result = await update_user(99999, update_data, db_session)

    # Assert
    assert result is None


# =============================================================================
# ProductRepositories тесты
# =============================================================================

@pytest.mark.asyncio
async def test_create_product(db_session: AsyncSession):
    """Создание товара."""
    # Arrange
    from src.db.schemas.Product import ProductCreate
    product_in = ProductCreate(
        product_id=200,
        name="New Product",
        brand="New Brand",
        subject="New Subject",
        entity="New Entity"
    )

    # Act
    product = await create_product(product_in, db_session)

    # Assert
    assert product is not None
    assert product.product_id == 200
    assert product.name == "New Product"


@pytest.mark.asyncio
async def test_read_product(db_session: AsyncSession, test_product):
    """Чтение товара по ID."""
    # Act
    product = await read_product(test_product.product_id, db_session)

    # Assert
    assert product is not None
    assert product.product_id == test_product.product_id


@pytest.mark.asyncio
async def test_read_product_not_found(db_session: AsyncSession):
    """Чтение несуществующего товара."""
    # Act
    product = await read_product(99999, db_session)

    # Assert
    assert product is None


@pytest.mark.asyncio
async def test_get_by_article(db_session: AsyncSession, test_product):
    """Получение товара по артикулу."""
    # Act
    product = await get_by_article(test_product.product_id, db_session)

    # Assert
    assert product is not None
    assert product.product_id == test_product.product_id


@pytest.mark.asyncio
async def test_get_by_article_not_found(db_session: AsyncSession):
    """Получение несуществующего товара по артикулу."""
    # Act
    product = await get_by_article(99999, db_session)

    # Assert
    assert product is None


@pytest.mark.asyncio
async def test_read_products(db_session: AsyncSession, test_product):
    """Чтение списка товаров."""
    # Act
    products = await read_products(db_session, skip=0, limit=10)

    # Assert
    assert len(products) >= 1


@pytest.mark.asyncio
async def test_read_products_with_filters(db_session: AsyncSession, test_product):
    """Чтение товаров с фильтром по бренду."""
    # Act
    products = await read_products(db_session, skip=0, limit=10, brand="Test")

    # Assert
    assert len(products) >= 1
    for p in products:
        assert p.brand == "Test"


# =============================================================================
# UserFavoriteRepositories тесты
# =============================================================================

@pytest.mark.asyncio
async def test_read_user_favorites(db_session: AsyncSession, test_user, test_product):
    """Чтение избранных товаров пользователя."""
    # Arrange
    fav = UserFavorite(user_id=test_user.id, product_id=test_product.product_id)
    db_session.add(fav)
    await db_session.commit()

    # Act
    favorites = await read_user_favorites(test_user.id, db_session)

    # Assert
    assert len(favorites) >= 1
    assert favorites[0].product_id == test_product.product_id


@pytest.mark.asyncio
async def test_read_user_favorites_empty(db_session: AsyncSession, test_user):
    """Чтение пустого списка избранного."""
    # Act
    favorites = await read_user_favorites(test_user.id, db_session)

    # Assert
    assert len(favorites) == 0


@pytest.mark.asyncio
async def test_create_user_favorites(db_session: AsyncSession, test_user, test_product):
    """Создание записи избранного."""
    # Arrange
    from src.db.schemas.UserFavorite import UserFavoriteCreate
    fav_in = UserFavoriteCreate(user_id=test_user.id, product_id=test_product.product_id)

    # Act
    fav = await create_user_favorites(fav_in, db_session)

    # Assert
    assert fav is not None
    assert fav.user_id == test_user.id
    assert fav.product_id == test_product.product_id


@pytest.mark.asyncio
async def test_create_user_favorites_duplicate(db_session: AsyncSession, test_user, test_product):
    """Создание дублирующейся записи избранного."""
    # Arrange
    from src.db.schemas.UserFavorite import UserFavoriteCreate
    fav_in = UserFavoriteCreate(user_id=test_user.id, product_id=test_product.product_id)
    
    # Создаем первую запись
    await create_user_favorites(fav_in, db_session)

    # Act - пытаемся создать дубликат
    fav = await create_user_favorites(fav_in, db_session)

    # Assert
    assert fav is None  # Дубликат не создается


@pytest.mark.asyncio
async def test_delete_user_favorites(db_session: AsyncSession, test_user, test_product):
    """Удаление записи из избранного."""
    # Arrange
    fav = UserFavorite(user_id=test_user.id, product_id=test_product.product_id)
    db_session.add(fav)
    await db_session.commit()

    # Act
    await delete_user_favorites(test_user.id, test_product.product_id, db_session)

    # Assert
    favorites = await read_user_favorites(test_user.id, db_session)
    assert len(favorites) == 0


@pytest.mark.asyncio
async def test_check_product_exists_true(db_session: AsyncSession, test_product):
    """Проверка существования товара (существует)."""
    # Act
    exists = await check_product_exists(test_product.product_id, db_session)

    # Assert
    assert exists is True


@pytest.mark.asyncio
async def test_check_product_exists_false(db_session: AsyncSession):
    """Проверка существования товара (не существует)."""
    # Act
    exists = await check_product_exists(99999, db_session)

    # Assert
    assert exists is False


# =============================================================================
# ProductRepositories - дополнительные тесты
# =============================================================================

@pytest.mark.asyncio
async def test_update_product(db_session: AsyncSession, test_product):
    """Обновление товара."""
    # Arrange
    from src.db.schemas.Product import ProductUpdate
    product_update = ProductUpdate(name="Updated Product", brand="Updated Brand")

    # Act
    updated = await update_product(test_product.product_id, product_update, db_session)

    # Assert
    assert updated is not None
    assert updated.name == "Updated Product"
    assert updated.brand == "Updated Brand"


@pytest.mark.asyncio
async def test_update_product_not_found(db_session: AsyncSession):
    """Обновление несуществующего товара."""
    # Arrange
    from src.db.schemas.Product import ProductUpdate
    product_update = ProductUpdate(name="Updated Product")

    # Act
    updated = await update_product(99999, product_update, db_session)

    # Assert
    assert updated is None


@pytest.mark.asyncio
async def test_delete_product(db_session: AsyncSession, test_product):
    """Удаление товара."""
    # Act
    await delete_product(test_product.id, db_session)

    # Assert
    product = await read_product(test_product.id, db_session)
    assert product is None


@pytest.mark.asyncio
async def test_get_product_detailed_stats(db_session: AsyncSession, test_product):
    """Получение детальной статистики товара."""
    # Arrange - создадим тестовые данные
    from datetime import date, timedelta
    
    # Цена
    price = PriceTS(product_id=test_product.product_id, dt=date.today(), price_sale=1000.0, discount_pct=10)
    db_session.add(price)
    
    # Остаток
    stock = StockTS(product_id=test_product.product_id, dt=date.today(), quantity=50)
    db_session.add(stock)
    
    # Продажи
    for i in range(5):
        sale = SalesProxyTS(
            product_id=test_product.product_id,
            dt=date.today() - timedelta(days=i),
            sales=10
        )
        db_session.add(sale)
    
    await db_session.commit()

    # Act
    stats = await get_product_detailed_stats(test_product.product_id, db_session)

    # Assert
    assert stats["price"] == 1000.0
    assert stats["stock"] == 50
    assert stats["avg_daily_sales"] > 0
    assert stats["days_to_oos"] is not None


# =============================================================================
# UserFavoriteRepositories - дополнительные тесты
# =============================================================================

@pytest.mark.asyncio
async def test_read_user_favorites_with_details(db_session: AsyncSession, test_user, test_product):
    """Чтение избранных товаров с деталями (цена, остаток)."""
    # Arrange
    from datetime import date
    
    fav = UserFavorite(user_id=test_user.id, product_id=test_product.product_id)
    db_session.add(fav)
    
    price = PriceTS(product_id=test_product.product_id, dt=date.today(), price_sale=1500.0, discount_pct=5)
    db_session.add(price)
    
    stock = StockTS(product_id=test_product.product_id, dt=date.today(), quantity=100)
    db_session.add(stock)
    
    await db_session.commit()

    # Act
    results = await read_user_favorites_with_details(test_user.id, db_session)

    # Assert
    assert len(results) >= 1
    prod, price_val, stock_val = results[0]
    assert prod.product_id == test_product.product_id
    assert price_val == 1500.0
    assert stock_val == 100


# =============================================================================
# UserRepositories - дополнительные тесты
# =============================================================================

@pytest.mark.asyncio
async def test_update_user_tg_id(db_session: AsyncSession, test_user):
    """Обновление Telegram ID пользователя."""
    # Arrange
    tg_id = 123456789

    # Act
    result = await update_user_tg_id(test_user.email, tg_id, db_session)

    # Assert
    assert result is True
    await db_session.refresh(test_user)
    assert test_user.user_id == tg_id


@pytest.mark.asyncio
async def test_update_user_tg_id_clear_existing(db_session: AsyncSession, test_user):
    """Обновление Telegram ID с очисткой у другого пользователя."""
    # Arrange
    # Создаём второго пользователя с тем же TG ID что будем устанавливать
    tg_id = 123456789
    user2 = User(email="user2@example.com", password_hash="hashed", role="user", user_id=tg_id)
    db_session.add(user2)
    await db_session.commit()
    
    # Act
    result = await update_user_tg_id(test_user.email, tg_id, db_session)

    # Assert
    assert result is True
    await db_session.refresh(test_user)
    await db_session.refresh(user2)
    assert test_user.user_id == tg_id
    assert user2.user_id is None  # Очищено


@pytest.mark.asyncio
async def test_update_user_tg_id_user_not_found(db_session: AsyncSession):
    """Обновление Telegram ID для несуществующего пользователя."""
    # Act
    result = await update_user_tg_id("nonexistent@example.com", 123456789, db_session)

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_delete_user(db_session: AsyncSession, test_user):
    """Удаление пользователя."""
    # Arrange
    user_id = test_user.id

    # Act
    await delete_user(test_user.user_id, db_session)

    # Assert
    from src.db.repositories.UserRepositories import read_user_by_internal_id
    user = await read_user_by_internal_id(user_id, db_session)
    assert user is None


@pytest.mark.asyncio
async def test_read_user_by_telegram_id(db_session: AsyncSession, test_user):
    """Чтение пользователя по Telegram ID."""
    # Arrange
    tg_id = 987654321
    test_user.user_id = tg_id
    await db_session.commit()

    # Act
    from src.db.repositories.UserRepositories import read_user_by_id
    user = await read_user_by_id(tg_id, db_session)

    # Assert
    assert user is not None
    assert user.user_id == tg_id


@pytest.mark.asyncio
async def test_read_user_by_telegram_id_not_found(db_session: AsyncSession):
    """Чтение несуществующего пользователя по Telegram ID."""
    # Act
    from src.db.repositories.UserRepositories import read_user_by_id
    user = await read_user_by_id(999999999, db_session)

    # Assert
    assert user is None
