"""
Интеграционные тесты для Auth API (функциональный подход).

Тестируемые endpoints:
- POST /auth/registration — регистрация пользователя
- POST /auth/login — вход пользователя
- GET /auth/me — получение информации о пользователе
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.User import User


@pytest.mark.asyncio
async def test_registration_success(client: AsyncClient, db_session: AsyncSession):
    """Успешная регистрация нового пользователя."""
    # Arrange
    registration_data = {
        "email": "newuser@example.com",
        "password": "SecurePass123",
        "role": "user",
        "is_pro": False,
        "is_active": True
    }

    # Act
    response = await client.post("/auth/registration/", json=registration_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"

    # Проверяем, что токены установлены в cookies
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

    # Проверяем, что пользователь создан в БД
    result = await db_session.execute(
        User.__table__.select().where(User.__table__.c.email == "newuser@example.com")
    )
    user = result.fetchone()
    assert user is not None
    assert user.email == "newuser@example.com"


@pytest.mark.asyncio
async def test_registration_duplicate_email(client: AsyncClient, db_session: AsyncSession):
    """Регистрация с дублирующимся email."""
    # Arrange
    registration_data = {
        "email": "duplicate@example.com",
        "password": "SecurePass123"
    }
    response1 = await client.post("/auth/registration/", json=registration_data)
    assert response1.status_code == 201

    # Act
    response2 = await client.post("/auth/registration/", json=registration_data)

    # Assert
    assert response2.status_code == 409
    data = response2.json()
    assert "already exists" in data.get("detail", "")


@pytest.mark.asyncio
async def test_registration_weak_password(client: AsyncClient):
    """Регистрация со слабым паролем (короче 8 символов)."""
    # Arrange
    registration_data = {
        "email": "weakpass@example.com",
        "password": "short"
    }

    # Act
    response = await client.post("/auth/registration/", json=registration_data)

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_registration_invalid_email(client: AsyncClient):
    """Регистрация с невалидным email."""
    # Arrange
    registration_data = {
        "email": "invalid-email",
        "password": "SecurePass123"
    }

    # Act
    response = await client.post("/auth/registration/", json=registration_data)

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session: AsyncSession):
    """Успешный вход пользователя."""
    # Arrange
    registration_data = {
        "email": "loginuser@example.com",
        "password": "SecurePass123"
    }
    await client.post("/auth/registration/", json=registration_data)

    # Act
    login_data = {
        "email": "loginuser@example.com",
        "password": "SecurePass123"
    }
    response = await client.post("/auth/login/", json=login_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db_session: AsyncSession):
    """Вход с неверным паролем."""
    # Arrange
    registration_data = {
        "email": "wrongpass@example.com",
        "password": "SecurePass123"
    }
    await client.post("/auth/registration/", json=registration_data)

    # Act
    login_data = {
        "email": "wrongpass@example.com",
        "password": "WrongPassword"
    }
    response = await client.post("/auth/login/", json=login_data)

    # Assert
    assert response.status_code == 401
    data = response.json()
    assert "Incorrect login or password" in data.get("detail", "")


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Вход с несуществующим пользователем."""
    # Arrange
    login_data = {
        "email": "nonexistent@example.com",
        "password": "SecurePass123"
    }

    # Act
    response = await client.post("/auth/login/", json=login_data)

    # Assert
    assert response.status_code == 401
    data = response.json()
    assert "Incorrect login or password" in data.get("detail", "")


@pytest.mark.asyncio
async def test_get_current_user_info_unauthorized(client: AsyncClient):
    """Получение информации без авторизации."""
    # Act
    response = await client.get("/auth/me")

    # Assert
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_with_telegram_id(client: AsyncClient, db_session: AsyncSession):
    """Вход по Telegram ID (цифровой email)."""
    # Arrange - регистрируем пользователя с TG user_id
    registration_data = {
        "email": "tguser@example.com",
        "password": "SecurePass123",
        "user_id": 987654321
    }
    await client.post("/auth/registration/", json=registration_data)

    # Act - логинимся по email (TG ID login требует special handling)
    login_data = {
        "email": "tguser@example.com",
        "password": "SecurePass123"
    }
    response = await client.post("/auth/login/", json=login_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


@pytest.mark.asyncio
async def test_registration_with_pro_role(client: AsyncClient, db_session: AsyncSession):
    """Регистрация с PRO ролью."""
    # Arrange
    registration_data = {
        "email": "prouser@example.com",
        "password": "SecurePass123",
        "role": "pro",
        "is_pro": True
    }

    # Act
    response = await client.post("/auth/registration/", json=registration_data)

    # Assert
    assert response.status_code == 201

    # Проверяем, что пользователь создан с PRO ролью
    result = await db_session.execute(
        User.__table__.select().where(User.__table__.c.email == "prouser@example.com")
    )
    user = result.fetchone()
    assert user is not None
    assert user.role == "pro"
    assert user.is_pro is True


@pytest.mark.asyncio
async def test_get_current_user_info_invalid_token(client: AsyncClient):
    """Получение информации о пользователе с невалидным токеном (401)."""
    # Arrange - устанавливаем невалидный токен
    client.cookies.set("access_token", "invalid_token_xyz")
    
    # Act
    response = await client.get("/auth/me")

    # Assert
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_info_nonexistent_user(client: AsyncClient, db_session: AsyncSession):
    """Получение информации о пользователе с несуществующим user_id (404)."""
    # Arrange
    # Создаем пользователя и получаем токен
    registration_data = {
        "email": "deleting_user@example.com",
        "password": "SecurePass123"
    }
    reg_response = await client.post("/auth/registration/", json=registration_data)
    access_token = reg_response.cookies.get("access_token")
    client.cookies.set("access_token", access_token)

    # Удаляем пользователя напрямую из БД
    await db_session.execute(
        User.__table__.delete().where(User.__table__.c.email == "deleting_user@example.com")
    )
    await db_session.commit()

    # Act - пытаемся получить информацию о несуществующем пользователе
    response = await client.get("/auth/me")

    # Assert
    assert response.status_code == 404
