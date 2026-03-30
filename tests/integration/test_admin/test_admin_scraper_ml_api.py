"""
Интеграционные тесты для Admin Scraper и ML API.

Тестируемые endpoints:
- POST /admin/sales/full-payload — полный пакет данных
- POST /admin/sales/analytics — загрузка остатков + расчёт продаж
- POST /admin/scraper/run — запуск скрапера (202 Accepted)
- POST /admin/ml/train — запуск обучения (202 Accepted)
- POST /admin/ml/forecast — запуск прогноза (202 Accepted)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from src.db.models.Product import Product


@pytest.fixture
async def test_product_for_payload(db_session: AsyncSession):
    """Фикстура: тестовый товар для payload тестов."""
    product = Product(
        product_id=8001,
        name="Test Product Payload",
        brand="TestBrand",
        subject="TestCategory",
        entity="TestEntity"
    )
    db_session.add(product)
    await db_session.commit()
    return product


@pytest.mark.asyncio
async def test_admin_process_full_payload_success(admin_client, test_product_for_payload):
    """Успешная обработка полного пакета данных."""
    # Arrange
    client, access_token = admin_client
    
    payload = {
        "products": [
            {"product_id": test_product_for_payload.product_id, "name": "Updated Product", "brand": "Brand", "subject": "Cat", "entity": "Entity"}
        ],
        "stocks": [
            {"product_id": test_product_for_payload.product_id, "dt": str(date.today()), "quantity": 100}
        ],
        "prices": [
            {"product_id": test_product_for_payload.product_id, "dt": str(date.today()), "price_sale": 1500.0, "discount_pct": 10}
        ],
        "deliveries": [
            {"product_id": test_product_for_payload.product_id, "dt": str(date.today()), "delivery_days": 3}
        ],
        "socials": [
            {"product_id": test_product_for_payload.product_id, "dt": str(date.today()), "rating": 4.5, "feedbacks": 50}
        ]
    }

    # Act
    response = await client.post("/admin/sales/full-payload", json=payload)

    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_stock_and_calculate_sales(admin_client, test_product_for_payload):
    """Загрузка остатков и автоматический расчёт продаж."""
    # Arrange
    client, access_token = admin_client
    
    stocks = [
        {"product_id": test_product_for_payload.product_id, "dt": str(date.today()), "quantity": 100},
        {"product_id": test_product_for_payload.product_id, "dt": str(date.today().replace(day=1)), "quantity": 150}
    ]

    # Act
    response = await client.post("/admin/sales/analytics", json=stocks)

    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_run_scraper_success(admin_client, mocker):
    """Запуск скрапера (202 Accepted)."""
    # Arrange
    client, access_token = admin_client
    article = 12345678
    
    # Мокируем background task чтобы не делать реальный запрос к WB
    mocker.patch("src.services.ProductService.seeding_single_product")

    # Act
    response = await client.post(f"/admin/scraper/run?article={article}")

    # Assert
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert str(article) in data["message"]


@pytest.mark.asyncio
async def test_admin_run_scraper_no_admin(regular_client):
    """Запуск скрапера без admin прав (401)."""
    # Arrange
    client, access_token = regular_client

    # Act
    response = await client.post("/admin/scraper/run?article=12345")

    # Assert
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_run_model_training(admin_client):
    """Запуск обучения модели (202 Accepted)."""
    # Arrange
    client, access_token = admin_client

    # Act
    response = await client.post("/admin/ml/train")

    # Assert
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert "обучение" in data["message"].lower() or "training" in data["message"].lower()


@pytest.mark.asyncio
async def test_admin_run_daily_forecast(admin_client):
    """Запуск ежедневного прогноза (202 Accepted)."""
    # Arrange
    client, access_token = admin_client

    # Act
    response = await client.post("/admin/ml/forecast")

    # Assert
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert "прогноз" in data["message"].lower() or "forecast" in data["message"].lower()


@pytest.mark.asyncio
async def test_admin_ml_no_admin(regular_client):
    """Запуск ML задач без admin прав (401)."""
    # Arrange
    client, access_token = regular_client

    # Act
    response = await client.post("/admin/ml/train")

    # Assert
    assert response.status_code == 401
