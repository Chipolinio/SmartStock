"""
Интеграционные тесты для Admin Sales API.

Тестируемые endpoints:
- POST /admin/sales/stock — создание остатков
- POST /admin/sales/stock/bulk — массовое создание остатков
- POST /admin/sales/sale — создание продаж
- POST /admin/sales/sale/bulk — массовое создание продаж
- POST /admin/sales/price — создание цен
- POST /admin/sales/price/bulk — массовое создание цен
- POST /admin/sales/delivery — создание доставки
- POST /admin/sales/delivery/bulk — массовое создание доставки
- POST /admin/sales/social — создание социальных данных
- POST /admin/sales/social/bulk — массовое создание социальных данных
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.db.models.Product import Product
from src.db.models.StockTS import StockTS
from src.db.models.SalesProxyTS import SalesProxyTS
from src.db.models.PriceTS import PriceTS


@pytest.fixture
async def test_product(db_session: AsyncSession):
    """Фикстура: тестовый товар."""
    product = Product(
        product_id=9001,
        name="Test Product for Sales",
        brand="TestBrand",
        subject="TestCategory",
        entity="TestEntity"
    )
    db_session.add(product)
    await db_session.commit()
    return product


@pytest.mark.asyncio
async def test_admin_create_stock_success(admin_client, db_session: AsyncSession, test_product):
    """Успешное создание записи остатков."""
    # Arrange
    client, access_token = admin_client
    stock_data = {
        "product_id": test_product.product_id,
        "dt": str(date.today()),
        "quantity": 100
    }

    # Act
    response = await client.post("/admin/sales/stock", json=stock_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 100


@pytest.mark.asyncio
async def test_admin_create_stocks_bulk_success(admin_client, test_product):
    """Массовое создание записей остатков."""
    # Arrange
    client, access_token = admin_client
    today = date.today()
    stocks_data = [
        {"product_id": test_product.product_id, "dt": str(today - timedelta(days=i)), "quantity": 100 - i * 5}
        for i in range(5)
    ]

    # Act
    response = await client.post("/admin/sales/stock/bulk", json=stocks_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 5


@pytest.mark.asyncio
async def test_admin_create_sale_success(admin_client, test_product):
    """Успешное создание записи продаж."""
    # Arrange
    client, access_token = admin_client
    sale_data = {
        "product_id": test_product.product_id,
        "dt": str(date.today()),
        "sales": 10,
        "confidence": 0.9
    }

    # Act
    response = await client.post("/admin/sales/sale", json=sale_data)

    # Assert
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_admin_create_sales_bulk_success(admin_client, test_product):
    """Массовое создание записей продаж."""
    # Arrange
    client, access_token = admin_client
    today = date.today()
    sales_data = [
        {"product_id": test_product.product_id, "dt": str(today - timedelta(days=i)), "sales": 5, "confidence": 0.8}
        for i in range(3)
    ]

    # Act
    response = await client.post("/admin/sales/sale/bulk", json=sales_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_admin_create_price_success(admin_client, test_product):
    """Успешное создание записи цены."""
    # Arrange
    client, access_token = admin_client
    price_data = {
        "product_id": test_product.product_id,
        "dt": str(date.today()),
        "price_sale": 2000.0,
        "discount_pct": 15
    }

    # Act
    response = await client.post("/admin/sales/price", json=price_data)

    # Assert
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_admin_create_prices_bulk_success(admin_client, test_product):
    """Массовое создание записей цен."""
    # Arrange
    client, access_token = admin_client
    today = date.today()
    prices_data = [
        {"product_id": test_product.product_id, "dt": str(today - timedelta(days=i)), "price_sale": 1000.0 + i * 50, "discount_pct": 10}
        for i in range(3)
    ]

    # Act
    response = await client.post("/admin/sales/price/bulk", json=prices_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_admin_create_delivery_success(admin_client, test_product):
    """Успешное создание записи доставки."""
    # Arrange
    client, access_token = admin_client
    delivery_data = {
        "product_id": test_product.product_id,
        "dt": str(date.today()),
        "delivery_days": 5
    }

    # Act
    response = await client.post("/admin/sales/delivery", json=delivery_data)

    # Assert
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_admin_create_deliveries_bulk_success(admin_client, test_product):
    """Массовое создание записей доставки."""
    # Arrange
    client, access_token = admin_client
    today = date.today()
    deliveries_data = [
        {"product_id": test_product.product_id, "dt": str(today - timedelta(days=i)), "delivery_days": 3}
        for i in range(3)
    ]

    # Act
    response = await client.post("/admin/sales/delivery/bulk", json=deliveries_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_admin_create_social_success(admin_client, test_product):
    """Успешное создание записи социальных данных."""
    # Arrange
    client, access_token = admin_client
    social_data = {
        "product_id": test_product.product_id,
        "dt": str(date.today()),
        "rating": 4.5,
        "feedbacks": 100
    }

    # Act
    response = await client.post("/admin/sales/social", json=social_data)

    # Assert
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_admin_create_socials_bulk_success(admin_client, test_product):
    """Массовое создание записей социальных данных."""
    # Arrange
    client, access_token = admin_client
    today = date.today()
    socials_data = [
        {"product_id": test_product.product_id, "dt": str(today - timedelta(days=i)), "rating": 4.0 + i * 0.1, "feedbacks": 50 + i * 10}
        for i in range(3)
    ]

    # Act
    response = await client.post("/admin/sales/social/bulk", json=socials_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_admin_sales_no_admin(regular_client, test_product):
    """Создание записей продаж без admin прав (401)."""
    # Arrange
    client, access_token = regular_client
    stock_data = {
        "product_id": test_product.product_id,
        "dt": str(date.today()),
        "quantity": 50
    }

    # Act
    response = await client.post("/admin/sales/stock", json=stock_data)

    # Assert
    assert response.status_code == 401
