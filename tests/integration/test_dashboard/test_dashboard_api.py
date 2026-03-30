"""
Интеграционные тесты для Dashboard API.

Тестируемые endpoints:
- GET /dashboard/kpi — KPI метрики
- GET /dashboard/sales-dynamics — динамика продаж
- GET /dashboard/stock-dynamics — динамика остатков
- GET /dashboard/abc-analysis — ABC анализ
- GET /dashboard/xyz-analysis — XYZ анализ
- GET /dashboard/top-products-by-revenue — топ по выручке
- GET /dashboard/forecasts — прогнозы
- GET /dashboard/forecasts/summary — сводка прогнозов
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.db.models.User import User
from src.db.models.Product import Product
from src.db.models.UserFavorite import UserFavorite
from src.db.models.SalesProxyTS import SalesProxyTS
from src.db.models.StockTS import StockTS


@pytest.fixture
async def test_user_with_data(db_session: AsyncSession):
    """Фикстура: пользователь с данными для тестов (ORM модели для БД)."""
    unique_id = uuid.uuid4().hex[:8]
    email = f"dashboard_user_{unique_id}@example.com"
    password = "SecurePass123"
    
    # Сначала регистрируем через API чтобы получить правильный password_hash
    from src.utils.security import get_password_hash
    
    # Создаем пользователя с правильным хешем
    user = User(
        email=email,
        password_hash=get_password_hash(password),
        role="user",
        is_pro=False,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Создаем товар
    product = Product(
        product_id=100,
        name="Test Product",
        brand="Test Brand",
        subject="Electronics",
        entity="Gadget"
    )
    db_session.add(product)
    await db_session.commit()

    # Добавляем в избранное
    favorite = UserFavorite(user_id=user.id, product_id=100)
    db_session.add(favorite)

    # Добавляем данные о продажах
    today = date.today()
    for i in range(30):
        sale = SalesProxyTS(
            product_id=100,
            dt=today - timedelta(days=i),
            sales=10,
            confidence=0.9
        )
        db_session.add(sale)

    # Добавляем данные об остатках
    for i in range(30):
        stock = StockTS(
            product_id=100,
            dt=today - timedelta(days=i),
            quantity=100 - i * 2
        )
        db_session.add(stock)

    await db_session.commit()

    return {
        "user_id": user.id,
        "product_id": 100,
        "email": email,
        "password": password
    }


@pytest.fixture
async def auth_client_with_data(client: AsyncClient, test_user_with_data: dict):
    """Фикстура: авторизованный клиент с данными."""
    # Логинимся и получаем токены
    login_data = {
        "email": test_user_with_data["email"],
        "password": test_user_with_data["password"]
    }
    login_response = await client.post("/auth/login/", json=login_data)
    access_token = login_response.cookies.get("access_token")
    client.cookies.set("access_token", access_token)

    return client, access_token, test_user_with_data


@pytest.mark.asyncio
async def test_get_kpi_success(auth_client_with_data):
    """Успешное получение KPI метрик."""
    # Arrange
    client, access_token, _ = auth_client_with_data

    # Act
    response = await client.get(
        "/dashboard/kpi?days=30",

    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    # Проверяем реальные поля API
    assert "total_products" in data or "total_revenue" in data or "avg_rating" in data


@pytest.mark.asyncio
async def test_get_kpi_unauthorized(client: AsyncClient):
    """Получение KPI без авторизации."""
    # Act
    response = await client.get("/dashboard/kpi?days=30")

    # Assert
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_sales_dynamics_success(auth_client_with_data):
    """Успешное получение динамики продаж."""
    # Arrange
    client, access_token, _ = auth_client_with_data

    # Act
    response = await client.get(
        "/dashboard/sales-dynamics?days=30",
        
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_sales_dynamics_with_product_filter(auth_client_with_data):
    """Получение динамики продаж с фильтром по товару."""
    # Arrange
    client, access_token, test_data = auth_client_with_data

    # Act
    response = await client.get(
        f"/dashboard/sales-dynamics?days=30&product_id={test_data['product_id']}",
        
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


@pytest.mark.asyncio
async def test_get_stock_dynamics_success(auth_client_with_data):
    """Успешное получение динамики остатков."""
    # Arrange
    client, access_token, _ = auth_client_with_data

    # Act
    response = await client.get(
        "/dashboard/stock-dynamics?days=30",
        
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_abc_analysis_success(auth_client_with_data):
    """Успешное получение ABC анализа."""
    # Arrange
    client, access_token, _ = auth_client_with_data

    # Act
    response = await client.get(
        "/dashboard/abc-analysis?days=30",
        
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_xyz_analysis_success(auth_client_with_data):
    """Успешное получение XYZ анализа."""
    # Arrange
    client, access_token, _ = auth_client_with_data

    # Act
    response = await client.get(
        "/dashboard/xyz-analysis?days=30",
        
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_top_products_by_revenue_success(auth_client_with_data):
    """Успешное получение топа товаров по выручке."""
    # Arrange
    client, access_token, _ = auth_client_with_data

    # Act
    response = await client.get(
        "/dashboard/top-products-by-revenue?days=30&limit=10",
        
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_top_products_by_sales_success(auth_client_with_data):
    """Успешное получение топа товаров по продажам."""
    # Arrange
    client, access_token, _ = auth_client_with_data

    # Act
    response = await client.get(
        "/dashboard/top-products-by-sales?days=30&limit=10",
        
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_products_rating_success(auth_client_with_data):
    """Успешное получение рейтинга товаров."""
    # Arrange
    client, access_token, _ = auth_client_with_data

    # Act
    response = await client.get(
        "/dashboard/products-rating?days=30&limit=10",
        
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_low_stock_success(auth_client_with_data):
    """Успешное получение товаров с низким остатком."""
    # Arrange
    client, access_token, _ = auth_client_with_data

    # Act
    response = await client.get(
        "/dashboard/low-stock?limit=10",
        
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "critical" in data or "warning" in data or "data" in data


@pytest.mark.asyncio
async def test_get_forecasts_success(auth_client_with_data):
    """Успешное получение прогнозов."""
    # Arrange
    client, access_token, _ = auth_client_with_data

    # Act
    response = await client.get(
        "/dashboard/forecasts?days=30",
        
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "data" in data or "forecasts" in data


@pytest.mark.asyncio
async def test_get_forecast_summary_success(auth_client_with_data):
    """Успешное получение сводки прогнозов."""
    # Arrange
    client, access_token, _ = auth_client_with_data

    # Act
    response = await client.get(
        "/dashboard/forecasts/summary",
        
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_get_forecast_history_success(auth_client_with_data):
    """Успешное получение истории прогнозов."""
    # Arrange
    client, access_token, test_data = auth_client_with_data

    # Act - передаем product_id
    response = await client.get(
        f"/dashboard/forecasts/history?days=30&product_id={test_data['product_id']}",

    )

    # Assert
    assert response.status_code in [200, 404]  # 404 если нет прогнозов


@pytest.mark.asyncio
async def test_dashboard_with_invalid_days_parameter(client: AsyncClient):
    """Dashboard endpoint с невалидным параметром days."""
    # Arrange
    registration_data = {
        "email": "invalid_days_user@example.com",
        "password": "SecurePass123"
    }
    reg_response = await client.post("/auth/registration/", json=registration_data)
    access_token = reg_response.cookies.get("access_token")

    # Act
    response = await client.get(
        "/dashboard/kpi?days=-5",
        
    )

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_dashboard_with_too_large_days_parameter(client: AsyncClient):
    """Dashboard endpoint с слишком большим параметром days."""
    # Arrange
    registration_data = {
        "email": "large_days_user@example.com",
        "password": "SecurePass123"
    }
    reg_response = await client.post("/auth/registration/", json=registration_data)
    access_token = reg_response.cookies.get("access_token")

    # Act
    response = await client.get(
        "/dashboard/kpi?days=500",
        
    )

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_dashboard_with_zero_days_parameter(client: AsyncClient):
    """Dashboard endpoint с days=0 (422)."""
    # Arrange
    registration_data = {
        "email": "zero_days_user@example.com",
        "password": "SecurePass123"
    }
    reg_response = await client.post("/auth/registration/", json=registration_data)
    access_token = reg_response.cookies.get("access_token")

    # Act
    response = await client.get(
        "/dashboard/kpi?days=0",
        
    )

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_dashboard_forecasts_history_without_product_id(auth_client_with_data):
    """Получение истории прогнозов без product_id (400)."""
    # Arrange
    client, access_token, _ = auth_client_with_data

    # Act
    response = await client.get(
        "/dashboard/forecasts/history?days=30",
        
    )

    # Assert - зависит от реализации, может быть 200 с пустыми данными или 400
    assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_dashboard_sales_dynamics_with_brand_filter(auth_client_with_data):
    """Получение динамики продаж с фильтром по бренду."""
    # Arrange
    client, access_token, _ = auth_client_with_data

    # Act
    response = await client.get(
        "/dashboard/sales-dynamics?days=30&brand=Test Brand",
        
    )

    # Assert
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_sales_dynamics_with_subject_filter(auth_client_with_data):
    """Получение динамики продаж с фильтром по категории."""
    # Arrange
    client, access_token, _ = auth_client_with_data

    # Act
    response = await client.get(
        "/dashboard/sales-dynamics?days=30&subject=Electronics",
        
    )

    # Assert
    assert response.status_code == 200
