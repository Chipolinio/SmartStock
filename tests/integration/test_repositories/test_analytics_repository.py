"""
Интеграционные тесты для AnalyticsRepository.

Тестируемые методы:
- get_sales_history
- get_stock_dynamics
- get_abc_data
- get_xyz_data
- get_top_products_by_revenue
- get_top_products_by_sales
- get_products_rating
- get_dashboard_kpi
- get_low_stock
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.db.models.User import User
from src.db.models.Product import Product
from src.db.models.UserFavorite import UserFavorite
from src.db.models.SalesProxyTS import SalesProxyTS
from src.db.models.PriceTS import PriceTS
from src.db.models.StockTS import StockTS
from src.db.models.SocialTS import SocialTS
from src.db.models.DeliveryTS import DeliveryTS

from src.db.repositories.AnalyticsRepository import (
    get_sales_history,
    get_stock_dynamics,
    get_abc_data,
    get_xyz_data,
    get_top_products_by_revenue,
    get_top_products_by_sales,
    get_products_rating,
    get_dashboard_kpi,
    get_low_stock,
)


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Фикстура: тестовый пользователь."""
    user = User(email="analytics_test@example.com", password_hash="hashed", role="user")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def analytics_products(db_session: AsyncSession, test_user):
    """Фикстура: набор товаров для аналитики."""
    products = []
    for i in range(5):
        product = Product(
            product_id=1000 + i,
            name=f"Analytics Product {i}",
            brand="TestBrand",
            subject="TestCategory",
            entity="TestEntity"
        )
        db_session.add(product)
        products.append(product)
        
        # Добавляем в избранное пользователя
        fav = UserFavorite(user_id=test_user.id, product_id=product.product_id)
        db_session.add(fav)
    
    await db_session.commit()
    return products


@pytest.fixture
async def sales_data(db_session: AsyncSession, analytics_products):
    """Фикстура: данные о продажах."""
    sales = []
    for product in analytics_products:
        for days_ago in range(30):
            sale = SalesProxyTS(
                product_id=product.product_id,
                dt=date.today() - timedelta(days=days_ago),
                sales=10 + product.product_id  # Разные продажи для разных товаров
            )
            db_session.add(sale)
            sales.append(sale)
    
    await db_session.commit()
    return sales


@pytest.fixture
async def price_data(db_session: AsyncSession, analytics_products):
    """Фикстура: данные о ценах."""
    prices = []
    for product in analytics_products:
        for days_ago in range(30):
            price = PriceTS(
                product_id=product.product_id,
                dt=date.today() - timedelta(days=days_ago),
                price_sale=1000.0 + product.product_id * 100,
                discount_pct=10
            )
            db_session.add(price)
            prices.append(price)
    
    await db_session.commit()
    return prices


@pytest.fixture
async def stock_data(db_session: AsyncSession, analytics_products):
    """Фикстура: данные об остатках."""
    stocks = []
    for product in analytics_products:
        for days_ago in range(30):
            stock = StockTS(
                product_id=product.product_id,
                dt=date.today() - timedelta(days=days_ago),
                quantity=100 - days_ago  # Уменьшающийся остаток
            )
            db_session.add(stock)
            stocks.append(stock)
    
    await db_session.commit()
    return stocks


@pytest.fixture
async def social_data(db_session: AsyncSession, analytics_products):
    """Фикстура: социальные данные (рейтинги, отзывы)."""
    socials = []
    for product in analytics_products:
        for days_ago in range(30):
            social = SocialTS(
                product_id=product.product_id,
                dt=date.today() - timedelta(days=days_ago),
                rating=4.0 + (product.product_id % 5) * 0.2,
                feedbacks=50 + product.product_id * 10
            )
            db_session.add(social)
            socials.append(social)
    
    await db_session.commit()
    return socials


@pytest.fixture
async def delivery_data(db_session: AsyncSession, analytics_products):
    """Фикстура: данные о доставке."""
    deliveries = []
    for product in analytics_products:
        for days_ago in range(30):
            delivery = DeliveryTS(
                product_id=product.product_id,
                dt=date.today() - timedelta(days=days_ago),
                delivery_days=5 + product.product_id % 3
            )
            db_session.add(delivery)
            deliveries.append(delivery)
    
    await db_session.commit()
    return deliveries


# =============================================================================
# get_sales_history тесты
# =============================================================================

@pytest.mark.asyncio
async def test_get_sales_history_single_product(
    db_session: AsyncSession,
    analytics_products,
    sales_data,
    price_data
):
    """Временной ряд продаж для одного товара."""
    # Act
    result = await get_sales_history(
        db_session,
        days=30,
        product_id=analytics_products[0].product_id
    )

    # Assert
    assert result.product_id == analytics_products[0].product_id
    assert len(result.data) == 30
    assert all(entry.sales > 0 for entry in result.data)
    assert all(entry.revenue > 0 for entry in result.data)


@pytest.mark.asyncio
async def test_get_sales_history_aggregated(
    db_session: AsyncSession,
    test_user,
    analytics_products,
    sales_data,
    price_data
):
    """Агрегированный временной ряд продаж по всем товарам пользователя."""
    # Act
    result = await get_sales_history(
        db_session,
        days=30,
        user_id=test_user.id
    )

    # Assert
    assert result.product_id is None
    assert len(result.data) == 30
    # Агрегированные продажи должны быть больше чем для одного товара
    assert all(entry.sales > 0 for entry in result.data)


@pytest.mark.asyncio
async def test_get_sales_history_empty(db_session: AsyncSession, test_user):
    """Продажи при отсутствии данных."""
    # Act
    result = await get_sales_history(
        db_session,
        days=30,
        user_id=test_user.id
    )

    # Assert
    assert result.product_id is None
    assert len(result.data) == 0


@pytest.mark.asyncio
async def test_get_sales_history_with_brand_filter(
    db_session: AsyncSession,
    test_user,
    analytics_products,
    sales_data,
    price_data
):
    """Фильтрация продаж по бренду."""
    # Act
    result = await get_sales_history(
        db_session,
        days=30,
        user_id=test_user.id,
        brand="TestBrand"
    )

    # Assert
    assert len(result.data) == 30


# =============================================================================
# get_stock_dynamics тесты
# =============================================================================

@pytest.mark.asyncio
async def test_get_stock_dynamics_single_product(
    db_session: AsyncSession,
    analytics_products,
    stock_data
):
    """Динамика остатков для одного товара."""
    # Act
    result = await get_stock_dynamics(
        db_session,
        days=30,
        product_id=analytics_products[0].product_id
    )

    # Assert
    assert result.product_id == analytics_products[0].product_id
    assert len(result.data) == 30
    assert all(entry.quantity >= 0 for entry in result.data)


@pytest.mark.asyncio
async def test_get_stock_dynamics_aggregated(
    db_session: AsyncSession,
    test_user,
    analytics_products,
    stock_data
):
    """Агрегированная динамика остатков."""
    # Act
    result = await get_stock_dynamics(
        db_session,
        days=30,
        user_id=test_user.id
    )

    # Assert
    assert result.product_id is None
    assert len(result.data) == 30


@pytest.mark.asyncio
async def test_get_stock_dynamics_empty(db_session: AsyncSession, test_user):
    """Динамика остатков при отсутствии данных."""
    # Act
    result = await get_stock_dynamics(
        db_session,
        days=30,
        user_id=test_user.id
    )

    # Assert
    assert result.product_id is None
    assert len(result.data) == 0


# =============================================================================
# get_abc_data тесты
# =============================================================================

@pytest.mark.asyncio
async def test_get_abc_data(db_session: AsyncSession, test_user, analytics_products, sales_data, price_data):
    """ABC-анализ товаров."""
    # Act
    result = await get_abc_data(test_user.id, db_session, days=30)

    # Assert
    assert len(result.data) == 5
    # Проверяем наличие ABC классов
    abc_classes = {entry.abc_class for entry in result.data}
    assert "A" in abc_classes  # Должен быть хотя бы один товар класса A
    
    # Проверяем что revenue_share в сумме даёт ~1
    total_share = sum(entry.revenue_share for entry in result.data)
    assert 0.99 <= total_share <= 1.01


@pytest.mark.asyncio
async def test_get_abc_data_empty(db_session: AsyncSession, test_user):
    """ABC-анализ при отсутствии данных."""
    # Act
    result = await get_abc_data(test_user.id, db_session, days=30)

    # Assert
    assert len(result.data) == 0


@pytest.mark.asyncio
async def test_get_abc_data_with_subject_filter(
    db_session: AsyncSession,
    test_user,
    analytics_products,
    sales_data,
    price_data
):
    """ABC-анализ с фильтром по категории."""
    # Act
    result = await get_abc_data(test_user.id, db_session, days=30, subject="TestCategory")

    # Assert
    assert len(result.data) == 5


# =============================================================================
# get_xyz_data тесты
# =============================================================================

@pytest.mark.asyncio
async def test_get_xyz_data(db_session: AsyncSession, test_user, analytics_products, sales_data):
    """XYZ-анализ товаров."""
    # Act
    result = await get_xyz_data(test_user.id, db_session, days=30)

    # Assert
    assert len(result.data) == 5
    # Проверяем наличие XYZ классов
    xyz_classes = {entry.xyz_class for entry in result.data}
    assert len(xyz_classes) > 0
    
    # Проверяем расчёт CV
    for entry in result.data:
        assert entry.avg_sales >= 0
        assert entry.sales_std >= 0
        assert entry.cv >= 0
        assert entry.xyz_class in ["X", "Y", "Z"]


@pytest.mark.asyncio
async def test_get_xyz_data_empty(db_session: AsyncSession, test_user):
    """XYZ-анализ при отсутствии данных."""
    # Act
    result = await get_xyz_data(test_user.id, db_session, days=30)

    # Assert
    assert len(result.data) == 0


# =============================================================================
# get_top_products_by_revenue тесты
# =============================================================================

@pytest.mark.asyncio
async def test_get_top_products_by_revenue(
    db_session: AsyncSession,
    test_user,
    analytics_products,
    sales_data,
    price_data
):
    """Топ товаров по выручке."""
    # Act
    result = await get_top_products_by_revenue(test_user.id, db_session, limit=3, days=30)

    # Assert
    assert len(result.data) == 3
    # Проверяем что товары отсортированы по выручке
    for i in range(len(result.data) - 1):
        assert result.data[i].total_revenue >= result.data[i + 1].total_revenue
    # Проверяем ранги
    assert result.data[0].rank == 1
    assert result.data[1].rank == 2
    assert result.data[2].rank == 3


@pytest.mark.asyncio
async def test_get_top_products_by_revenue_empty(db_session: AsyncSession, test_user):
    """Топ товаров по выручке при отсутствии данных."""
    # Act
    result = await get_top_products_by_revenue(test_user.id, db_session, limit=10)

    # Assert
    assert len(result.data) == 0


# =============================================================================
# get_top_products_by_sales тесты
# =============================================================================

@pytest.mark.asyncio
async def test_get_top_products_by_sales(
    db_session: AsyncSession,
    test_user,
    analytics_products,
    sales_data,
    price_data
):
    """Топ товаров по количеству продаж."""
    # Act
    result = await get_top_products_by_sales(test_user.id, db_session, limit=3, days=30)

    # Assert
    assert len(result.data) == 3
    # Проверяем что товары отсортированы по продажам
    for i in range(len(result.data) - 1):
        assert result.data[i].total_sales >= result.data[i + 1].total_sales


@pytest.mark.asyncio
async def test_get_top_products_by_sales_empty(db_session: AsyncSession, test_user):
    """Топ товаров по продажам при отсутствии данных."""
    # Act
    result = await get_top_products_by_sales(test_user.id, db_session, limit=10)

    # Assert
    assert len(result.data) == 0


# =============================================================================
# get_products_rating тесты
# =============================================================================

@pytest.mark.asyncio
async def test_get_products_rating(
    db_session: AsyncSession,
    test_user,
    analytics_products,
    social_data
):
    """Рейтинг товаров."""
    # Act
    result = await get_products_rating(test_user.id, db_session, limit=3, days=30)

    # Assert
    assert len(result.data) == 3
    # Проверяем что товары отсортированы по рейтингу
    for i in range(len(result.data) - 1):
        assert result.data[i].avg_rating >= result.data[i + 1].avg_rating


@pytest.mark.asyncio
async def test_get_products_rating_empty(db_session: AsyncSession, test_user):
    """Рейтинг товаров при отсутствии данных."""
    # Act
    result = await get_products_rating(test_user.id, db_session, limit=10)

    # Assert
    assert len(result.data) == 0


# =============================================================================
# get_dashboard_kpi тесты
# =============================================================================

@pytest.mark.asyncio
async def test_get_dashboard_kpi(
    db_session: AsyncSession,
    test_user,
    analytics_products,
    sales_data,
    price_data,
    social_data,
    delivery_data,
    stock_data
):
    """KPI метрики дашборда."""
    # Act
    result = await get_dashboard_kpi(test_user.id, db_session, days=30)

    # Assert
    assert result.total_revenue > 0
    assert result.total_sales > 0
    assert result.avg_rating > 0
    assert result.total_products == 5
    assert result.avg_delivery_days is not None


@pytest.mark.asyncio
async def test_get_dashboard_kpi_empty(db_session: AsyncSession, test_user):
    """KPI метрики при отсутствии данных."""
    # Act
    result = await get_dashboard_kpi(test_user.id, db_session, days=30)

    # Assert
    assert result.total_revenue == 0.0
    assert result.total_sales == 0
    assert result.avg_rating == 0.0
    assert result.total_products == 0


# =============================================================================
# get_low_stock тесты
# =============================================================================

@pytest.mark.asyncio
async def test_get_low_stock(
    db_session: AsyncSession,
    test_user,
    analytics_products,
    sales_data,
    stock_data
):
    """Товары с низким остатком."""
    # Act
    result = await get_low_stock(test_user.id, db_session, limit=10)

    # Assert
    assert len(result.data) > 0
    for item in result.data:
        assert item.current_stock >= 0
        assert item.avg_sales > 0
        assert item.days_until_oos is not None
        assert item.status in ["critical", "warning", "ok"]


@pytest.mark.asyncio
async def test_get_low_stock_empty(db_session: AsyncSession, test_user):
    """Товары с низким остатком при отсутствии данных."""
    # Act
    result = await get_low_stock(test_user.id, db_session, limit=10)

    # Assert
    assert len(result.data) == 0
