"""
Интеграционные тесты для Admin Products API.

Тестируемые endpoints:
- POST /admin/products/ — создание товара
- POST /admin/products/bulk — массовое создание
- PATCH /admin/products/{id} — обновление товара
- DELETE /admin/products/{id} — удаление товара
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.Product import Product


@pytest.mark.asyncio
async def test_admin_create_product_success(admin_client, db_session: AsyncSession):
    """Успешное создание товара admin."""
    # Arrange
    client, access_token = admin_client
    product_data = {
        "product_id": 1001,
        "name": "Test Product Admin",
        "brand": "TestBrand",
        "subject": "TestCategory",
        "entity": "TestEntity"
    }

    # Act
    response = await client.post("/admin/products/", json=product_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] == 1001
    assert data["name"] == "Test Product Admin"

    # Проверяем, что товар создан в БД
    result = await db_session.execute(
        Product.__table__.select().where(Product.__table__.c.product_id == 1001)
    )
    product = result.fetchone()
    assert product is not None


@pytest.mark.asyncio
async def test_admin_create_product_duplicate(admin_client, db_session: AsyncSession):
    """Создание товара с дублирующимся product_id (409)."""
    # Arrange
    client, access_token = admin_client
    
    # Создаем первый товар
    product_data = {
        "product_id": 1002,
        "name": "Product A",
        "brand": "BrandA",
        "subject": "CatA",
        "entity": "EntityA"
    }
    await client.post("/admin/products/", json=product_data)

    # Act - пытаемся создать дубликат
    response = await client.post("/admin/products/", json=product_data)

    # Assert
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_admin_create_product_no_admin(regular_client, db_session: AsyncSession):
    """Создание товара без admin прав (401)."""
    # Arrange
    client, access_token = regular_client
    product_data = {
        "product_id": 1003,
        "name": "No Admin Product",
        "brand": "Brand",
        "subject": "Cat",
        "entity": "Entity"
    }

    # Act
    response = await client.post("/admin/products/", json=product_data)

    # Assert
    assert response.status_code == 401  # Access denied


@pytest.mark.asyncio
async def test_admin_create_products_bulk_success(admin_client, db_session: AsyncSession):
    """Успешное массовое создание товаров."""
    # Arrange
    client, access_token = admin_client
    products_data = [
        {"product_id": 2001, "name": "Bulk Product 1", "brand": "Brand1", "subject": "Cat1", "entity": "Entity1"},
        {"product_id": 2002, "name": "Bulk Product 2", "brand": "Brand2", "subject": "Cat2", "entity": "Entity2"},
        {"product_id": 2003, "name": "Bulk Product 3", "brand": "Brand3", "subject": "Cat3", "entity": "Entity3"},
    ]

    # Act
    response = await client.post("/admin/products/bulk", json=products_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_admin_create_products_bulk_empty(admin_client):
    """Массовое создание с пустым списком (возвращает 201 с [])."""
    # Arrange
    client, access_token = admin_client

    # Act
    response = await client.post("/admin/products/bulk", json=[])

    # Assert - сервер принимает пустой список и возвращает 201
    assert response.status_code == 201
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_admin_update_product_success(admin_client, db_session: AsyncSession):
    """Успешное обновление товара."""
    # Arrange
    client, access_token = admin_client
    
    # Создаем товар
    product_data = {
        "product_id": 3001,
        "name": "Product To Update",
        "brand": "OldBrand",
        "subject": "OldCat",
        "entity": "OldEntity"
    }
    await client.post("/admin/products/", json=product_data)

    # Act - обновляем
    update_data = {
        "name": "Updated Product Name",
        "brand": "NewBrand"
    }
    response = await client.patch(f"/admin/products/{3001}", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Product Name"
    assert data["brand"] == "NewBrand"


@pytest.mark.asyncio
async def test_admin_update_product_not_found(admin_client):
    """Обновление несуществующего товара (404)."""
    # Arrange
    client, access_token = admin_client
    update_data = {"name": "New Name"}

    # Act
    response = await client.patch("/admin/products/99999", json=update_data)

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_delete_product_success(admin_client, db_session: AsyncSession):
    """Успешное удаление товара."""
    # Arrange
    client, access_token = admin_client
    
    # Создаем товар
    product_data = {
        "product_id": 4001,
        "name": "Product To Delete",
        "brand": "Brand",
        "subject": "Cat",
        "entity": "Entity"
    }
    await client.post("/admin/products/", json=product_data)

    # Act - удаляем
    response = await client.delete(f"/admin/products/{4001}")

    # Assert
    assert response.status_code == 204

    # Проверяем, что товар удален из БД
    result = await db_session.execute(
        Product.__table__.select().where(Product.__table__.c.product_id == 4001)
    )
    product = result.fetchone()
    assert product is None


@pytest.mark.asyncio
async def test_admin_delete_product_not_found(admin_client):
    """Удаление несуществующего товара (404)."""
    # Arrange
    client, access_token = admin_client

    # Act
    response = await client.delete("/admin/products/99999")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_products_unauthorized(client: AsyncClient):
    """Доступ к admin endpoints без авторизации (401)."""
    # Arrange
    product_data = {
        "product_id": 5001,
        "name": "Unauthorized Product",
        "brand": "Brand",
        "subject": "Cat",
        "entity": "Entity"
    }

    # Act
    response = await client.post("/admin/products/", json=product_data)

    # Assert
    assert response.status_code == 401
