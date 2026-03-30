"""
Фикстуры для тестов Admin API.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.User import User


@pytest.fixture
async def admin_user(db_session: AsyncSession):
    """Фикстура: создание admin пользователя."""
    admin = User(
        email="admin@example.com",
        password_hash="hashed_admin_password",
        role="admin",
        is_pro=True,
        is_active=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def regular_user(db_session: AsyncSession):
    """Фикстура: создание обычного пользователя (не admin)."""
    user = User(
        email="regular@example.com",
        password_hash="hashed_password",
        role="user",
        is_pro=False,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_client(client: AsyncClient, db_session: AsyncSession):
    """Фикстура: авторизованный admin клиент.
    
    Создает пользователя и устанавливает роль admin напрямую в БД.
    """
    # Регистрируем нового пользователя
    await client.post("/auth/registration/", json={
        "email": "admin_test@example.com",
        "password": "SecurePass123"
    })
    
    # Логинимся
    await client.post("/auth/login/", json={
        "email": "admin_test@example.com",
        "password": "SecurePass123"
    })
    
    # Устанавливаем роль admin напрямую в БД
    await db_session.execute(
        User.__table__.update()
        .where(User.__table__.c.email == "admin_test@example.com")
        .values(role="admin", is_pro=True)
    )
    await db_session.commit()
    
    # Перелогиниваемся для получения токена с admin ролью
    login_response = await client.post("/auth/login/", json={
        "email": "admin_test@example.com",
        "password": "SecurePass123"
    })
    
    access_token = login_response.cookies.get("access_token")
    
    # Устанавливаем cookies на клиент
    client.cookies.set("access_token", access_token)
    
    return client, access_token


@pytest.fixture
async def regular_client(client: AsyncClient):
    """Фикстура: авторизованный обычный клиент (не admin)."""
    # Регистрируем обычного пользователя
    await client.post("/auth/registration/", json={
        "email": "regular_test@example.com",
        "password": "SecurePass123"
    })
    
    # Логинимся
    login_response = await client.post("/auth/login/", json={
        "email": "regular_test@example.com",
        "password": "SecurePass123"
    })
    
    access_token = login_response.cookies.get("access_token")
    
    # Устанавливаем cookies на клиент
    client.cookies.set("access_token", access_token)
    
    return client, access_token
