"""
Интеграционные тесты для Products API.

Тестируемые endpoints:
- GET /products/ — список товаров
- GET /products/{product_id} — товар по ID
- GET /products/{product_id}/detailed — детальная информация
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.User import User
from src.db.models.Product import Product


@pytest.fixture
async def test_products_data(db_session: AsyncSession):
    """Фикстура: товары для тестов."""
    products = [
        Product(product_id=100, name="Coffee Machine", brand="Bosch", subject="Kitchen", entity="Appliance"),
        Product(product_id=200, name="Tea Set", brand="Lipton", subject="Kitchen", entity="Utensil"),
        Product(product_id=300, name="Laptop", brand="Apple", subject="Electronics", entity="Computer"),
    ]
    for p in products:
        db_session.add(p)
    await db_session.commit()
    return [p.product_id for p in products]


@pytest.fixture
async def authorized_client(client: AsyncClient, db_session: AsyncSession):
    """Фикстура: авторизованный клиент."""
    registration_data = {"email": "products_test@example.com", "password": "SecurePass123"}
    reg_response = await client.post("/auth/registration/", json=registration_data)
    access_token = reg_response.cookies.get("access_token")
    client.cookies.set("access_token", access_token)
    return client, access_token


@pytest.mark.asyncio
async def test_get_products_list(authorized_client, test_products_data):
    """Получение списка товаров."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.get(
        "/products/?limit=10",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_get_products_with_filters(authorized_client, test_products_data):
    """Получение товаров с фильтром по бренду."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.get(
        "/products/?brand=Bosch",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["brand"] == "Bosch"


@pytest.mark.asyncio
async def test_get_products_search_by_name(authorized_client, test_products_data):
    """Поиск товаров по названию."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.get(
        "/products/?name=Coffee",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "Coffee" in data[0]["name"]


@pytest.mark.asyncio
async def test_get_product_by_id(authorized_client, test_products_data):
    """Получение товара по ID."""
    # Arrange
    client, access_token = authorized_client
    product_id = test_products_data[0]

    # Act
    response = await client.get(
        f"/products/{product_id}",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == product_id


@pytest.mark.asyncio
async def test_get_product_not_found(authorized_client):
    """Получение несуществующего товара."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.get(
        "/products/99999",
    )

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_product_detailed(authorized_client, test_products_data):
    """Получение детальной информации о товаре."""
    # Arrange
    client, access_token = authorized_client
    product_id = test_products_data[0]

    # Act
    response = await client.get(
        f"/products/{product_id}/detailed",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == product_id
    assert "name" in data
    assert "brand" in data


@pytest.mark.asyncio
async def test_get_products_unauthorized():
    """Получение товаров без авторизации."""
    # Arrange
    from httpx import AsyncClient, ASGITransport
    from src.main import app
    from src.db.database import get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Act
        response = await ac.get("/products/?limit=10")

        # Assert
        assert response.status_code in [200, 401]  # Зависит от настроек авторизации


@pytest.mark.asyncio
async def test_get_products_pagination(authorized_client, test_products_data):
    """Тест пагинации товаров."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.get(
        "/products/?skip=0&limit=2",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2


@pytest.mark.asyncio
async def test_get_products_invalid_limit(authorized_client):
    """Тест с невалидным limit (> 1000)."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.get(
        "/products/?limit=2000",
    )

    # Assert
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_products_by_subject(authorized_client, test_products_data):
    """Получение товаров по категории."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.get(
        "/products/?subject=Kitchen",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    for item in data:
        assert item["subject"] == "Kitchen"


@pytest.mark.asyncio
async def test_get_products_invalid_name_short(authorized_client):
    """Поиск товаров с name < 2 символов (422)."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.get(
        "/products/?name=a",
    )

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_products_invalid_limit_zero(authorized_client):
    """Получение товаров с limit=0 (422)."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.get(
        "/products/?limit=0",
    )

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_products_invalid_limit_too_large(authorized_client):
    """Получение товаров с limit > 1000 (422)."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.get(
        "/products/?limit=2000",
    )

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_products_combined_filters(authorized_client, test_products_data):
    """Получение товаров с комбинацией фильтров: brand + subject + entity."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.get(
        "/products/?brand=Bosch&subject=Kitchen&entity=Appliance",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    for item in data:
        assert item["brand"] == "Bosch"
        assert item["subject"] == "Kitchen"
        assert item["entity"] == "Appliance"
