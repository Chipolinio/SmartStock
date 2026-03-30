"""
Интеграционные тесты для Sales API.

Тестируемые endpoints:
- GET /sales/stock/{product_id} — история остатков
- GET /sales/sale/{product_id} — история продаж
- GET /sales/price/{product_id} — история цен
- GET /sales/delivery/{product_id} — история доставки
- GET /sales/social/{product_id} — история социальных данных
- GET /sales/predicted_sale/{product_id} — история прогнозов
- GET /sales/analytics/{product_id} — аналитика
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.db.models.User import User
from src.db.models.Product import Product
from src.db.models.StockTS import StockTS
from src.db.models.SalesProxyTS import SalesProxyTS
from src.db.models.PriceTS import PriceTS


@pytest.fixture
async def sales_test_data(db_session: AsyncSession):
    """Фикстура: данные для тестов sales."""
    # Создаем пользователя
    user = User(
        email="sales_test@example.com",
        password_hash="hashed",
        role="user",
        is_pro=False,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Создаем товар
    product = Product(product_id=100, name="Test Product", brand="Test", subject="Test", entity="Test")
    db_session.add(product)
    await db_session.commit()

    # Добавляем данные остатков за 30 дней
    today = date.today()
    for i in range(30):
        stock = StockTS(product_id=100, dt=today - timedelta(days=i), quantity=100 - i * 2)
        db_session.add(stock)

        sale = SalesProxyTS(product_id=100, dt=today - timedelta(days=i), sales=2, confidence=0.9)
        db_session.add(sale)

        price = PriceTS(product_id=100, dt=today - timedelta(days=i), price_sale=1000.0, discount_pct=10)
        db_session.add(price)

    await db_session.commit()

    return {"user_id": user.id, "product_id": 100}


@pytest.fixture
async def authorized_client(client: AsyncClient):
    """Фикстура: авторизованный клиент."""
    registration_data = {"email": "sales_api_test@example.com", "password": "SecurePass123"}
    reg_response = await client.post("/auth/registration/", json=registration_data)
    access_token = reg_response.cookies.get("access_token")
    return client, access_token


@pytest.mark.asyncio
async def test_get_stock_history(authorized_client, sales_test_data):
    """Получение истории остатков."""
    # Arrange
    client, access_token = authorized_client
    product_id = sales_test_data["product_id"]

    # Act
    response = await client.get(
        f"/sales/stock/{product_id}?limit=10",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 10


@pytest.mark.asyncio
async def test_get_sales_history(authorized_client, sales_test_data):
    """Получение истории продаж."""
    # Arrange
    client, access_token = authorized_client
    product_id = sales_test_data["product_id"]

    # Act
    response = await client.get(
        f"/sales/sale/{product_id}?limit=10",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 10


@pytest.mark.asyncio
async def test_get_prices_history(authorized_client, sales_test_data):
    """Получение истории цен."""
    # Arrange
    client, access_token = authorized_client
    product_id = sales_test_data["product_id"]

    # Act
    response = await client.get(
        f"/sales/price/{product_id}?limit=10",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 10


@pytest.mark.asyncio
async def test_get_delivery_history(authorized_client, sales_test_data):
    """Получение истории доставки."""
    # Arrange
    client, access_token = authorized_client
    product_id = sales_test_data["product_id"]

    # Act
    response = await client.get(
        f"/sales/delivery/{product_id}?limit=10",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_socials_history(authorized_client, sales_test_data):
    """Получение истории социальных данных."""
    # Arrange
    client, access_token = authorized_client
    product_id = sales_test_data["product_id"]

    # Act
    response = await client.get(
        f"/sales/social/{product_id}?limit=10",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_predicted_sales_history(authorized_client, sales_test_data):
    """Получение истории прогнозов продаж."""
    # Arrange
    client, access_token = authorized_client
    product_id = sales_test_data["product_id"]

    # Act
    response = await client.get(
        f"/sales/predicted_sale/{product_id}?limit=10",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_product_analytics(authorized_client, sales_test_data):
    """Получение аналитики по товару."""
    # Arrange
    client, access_token = authorized_client
    product_id = sales_test_data["product_id"]

    # Act
    response = await client.get(
        f"/sales/analytics/{product_id}",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "velocity" in data or "current_stock" in data or "days_to_oos" in data


@pytest.mark.asyncio
async def test_get_stock_history_invalid_limit(authorized_client, sales_test_data):
    """Получение истории с невалидным limit."""
    # Arrange
    client, access_token = authorized_client
    product_id = sales_test_data["product_id"]

    # Act
    response = await client.get(
        f"/sales/stock/{product_id}?limit=500",
    )

    # Assert
    assert response.status_code == 422  # Validation error (le=365)


@pytest.mark.asyncio
async def test_get_sales_history_for_nonexistent_product(authorized_client):
    """Получение истории продаж для несуществующего товара."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.get(
        "/sales/sale/99999?limit=10",
    )

    # Assert
    assert response.status_code == 200  # Пустой список
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_stock_history_unauthorized(client):
    """Получение истории остатков без авторизации (sales endpoints публичные)."""
    # Act
    response = await client.get("/sales/stock/100?limit=10")

    # Assert - sales endpoints публичные, возвращают 200 с пустыми данными
    assert response.status_code == 200
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_stock_history_invalid_limit_zero(authorized_client, sales_test_data):
    """Получение истории остатков с limit=0 (422)."""
    # Arrange
    client, access_token = authorized_client
    product_id = sales_test_data["product_id"]

    # Act
    response = await client.get(
        f"/sales/stock/{product_id}?limit=0",
    )

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_stock_history_invalid_limit_too_large(authorized_client, sales_test_data):
    """Получение истории остатков с limit > 365 (422)."""
    # Arrange
    client, access_token = authorized_client
    product_id = sales_test_data["product_id"]

    # Act
    response = await client.get(
        f"/sales/stock/{product_id}?limit=500",
    )

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_analytics_for_product_without_data(authorized_client, db_session: AsyncSession):
    """Получение аналитики для товара без данных."""
    # Arrange
    client, access_token = authorized_client
    
    # Создаем товар без данных
    product = Product(product_id=9999, name="No Data Product", brand="Test", subject="Test", entity="Test")
    db_session.add(product)
    await db_session.commit()

    # Act
    response = await client.get(
        "/sales/analytics/9999",
    )

    # Assert - зависит от реализации, может вернуть 200 с пустыми данными или 404
    assert response.status_code in [200, 404]
