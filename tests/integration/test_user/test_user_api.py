"""
Интеграционные тесты для User API.

Тестируемые endpoints:
- GET /user/favorites — список избранного
- POST /user/favorites — добавить в избранное
- DELETE /user/favorites/{product_id} — удалить из избранного
- GET /user/profile — профиль
- PATCH /user/profile — обновить профиль
- GET /user/telegram/info — информация о Telegram
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.User import User
from src.db.models.Product import Product
from src.db.models.UserFavorite import UserFavorite


@pytest.fixture
async def user_with_favorites(db_session: AsyncSession):
    """Фикстура: пользователь с избранными товарами."""
    # Создаем пользователя
    user = User(email="fav_test@example.com", password_hash="hashed", role="user")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Создаем товары
    products = [
        Product(product_id=100, name="Product 1", brand="Brand A", subject="Cat1", entity="E1"),
        Product(product_id=200, name="Product 2", brand="Brand B", subject="Cat2", entity="E2"),
    ]
    for p in products:
        db_session.add(p)
    await db_session.commit()

    # Добавляем в избранное
    fav = UserFavorite(user_id=user.id, product_id=100)
    db_session.add(fav)
    await db_session.commit()

    return {"user_id": user.id, "product_ids": [100, 200]}


@pytest.fixture
async def authorized_client(client: AsyncClient):
    """Фикстура: авторизованный клиент."""
    registration_data = {"email": "user_api_test@example.com", "password": "SecurePass123"}
    reg_response = await client.post("/auth/registration/", json=registration_data)
    access_token = reg_response.cookies.get("access_token")
    client.cookies.set("access_token", access_token)
    return client, access_token


@pytest.mark.asyncio
async def test_get_favorites(authorized_client, user_with_favorites, db_session):
    """Получение списка избранных товаров."""
    # Arrange
    client, access_token = authorized_client

    # Привязываем товар к пользователю теста
    user = await db_session.execute(User.__table__.select().where(User.__table__.c.email == "user_api_test@example.com"))
    user_row = user.fetchone()
    
    # Act
    response = await client.get(
        "/user/favorites",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_add_to_favorites_by_product_id(authorized_client, db_session):
    """Добавление товара в избранное по product_id."""
    # Arrange
    client, access_token = authorized_client
    
    # Создаем товар
    product = Product(product_id=500, name="Test Product", brand="Test", subject="Test", entity="Test")
    db_session.add(product)
    await db_session.commit()

    # Act
    response = await client.post(
        "/user/favorites",
        json={"product_id": 500},
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] is not None
    assert data["product_id"] == 500


@pytest.mark.asyncio
async def test_add_to_favorites_by_wb_article(authorized_client, mocker):
    """Добавление товара в избранное по wb_article (202 Accepted)."""
    # Arrange
    client, access_token = authorized_client
    
    # Мокируем background task чтобы не делать реальный запрос к WB
    mocker.patch("src.services.ProductService.seeding_single_product")

    # Act
    response = await client.post("/user/favorites?wb_article=123456")

    # Assert - должен вернуть 202 Accepted (товар не найден, запущен скрапер)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "processing"


@pytest.mark.asyncio
async def test_add_to_favorites_already_exists(authorized_client, db_session):
    """Добавление уже существующего в избранном товара."""
    # Arrange
    client, access_token = authorized_client
    
    # Создаем товар и добавляем в избранное
    product = Product(product_id=600, name="Test", brand="Test", subject="Test", entity="Test")
    db_session.add(product)
    await db_session.commit()
    
    user = await db_session.execute(User.__table__.select().where(User.__table__.c.email == "user_api_test@example.com"))
    user_row = user.fetchone()
    
    fav = UserFavorite(user_id=user_row.id, product_id=600)
    db_session.add(fav)
    await db_session.commit()

    # Act
    response = await client.post(
        "/user/favorites",
        json={"product_id": 600},
    )

    # Assert
    assert response.status_code == 409  # Conflict


@pytest.mark.asyncio
async def test_delete_from_favorites(authorized_client, db_session):
    """Удаление товара из избранного."""
    # Arrange
    client, access_token = authorized_client
    
    # Создаем товар и добавляем в избранное
    product = Product(product_id=700, name="Test", brand="Test", subject="Test", entity="Test")
    db_session.add(product)
    await db_session.commit()
    
    user = await db_session.execute(User.__table__.select().where(User.__table__.c.email == "user_api_test@example.com"))
    user_row = user.fetchone()
    
    fav = UserFavorite(user_id=user_row.id, product_id=700)
    db_session.add(fav)
    await db_session.commit()

    # Act
    response = await client.delete(
        f"/user/favorites/700",
    )

    # Assert
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_profile(authorized_client):
    """Получение профиля пользователя."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.get(
        "/user/profile",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert data["email"] == "user_api_test@example.com"


@pytest.mark.asyncio
async def test_update_profile_email(authorized_client):
    """Обновление email в профиле."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.patch(
        "/user/profile",
        json={"email": "newemail@example.com"},
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newemail@example.com"


@pytest.mark.asyncio
async def test_update_profile_empty_data(authorized_client):
    """Обновление профиля без данных."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.patch(
        "/user/profile",
        json={},
    )

    # Assert
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_telegram_info(authorized_client):
    """Получение информации о Telegram."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.get(
        "/user/telegram/info",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "is_linked" in data
    assert "telegram_id" in data


@pytest.mark.asyncio
async def test_link_telegram(authorized_client, db_session):
    """Привязка Telegram через бот."""
    # Arrange
    client, access_token = authorized_client
    
    user = await db_session.execute(User.__table__.select().where(User.__table__.c.email == "user_api_test@example.com"))
    user_row = user.fetchone()

    # Act
    response = await client.post(
        f"/user/telegram/link?telegram_id=123456&user_id={user_row.id}",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


@pytest.mark.asyncio
async def test_unlink_telegram(authorized_client, db_session):
    """Отвязка Telegram."""
    # Arrange
    client, access_token = authorized_client
    
    # Сначала привязываем
    user = await db_session.execute(User.__table__.select().where(User.__table__.c.email == "user_api_test@example.com"))
    user_row = user.fetchone()
    
    from src.services.UserService import link_telegram_by_bot
    await link_telegram_by_bot(987654, user_row.id, db_session)

    # Act
    response = await client.delete(
        "/user/telegram/unlink",
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


@pytest.mark.asyncio
async def test_favorites_unauthorized():
    """Получение избранного без авторизации."""
    # Arrange
    from httpx import AsyncClient, ASGITransport
    from src.main import app
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Act
        response = await ac.get("/user/favorites")

        # Assert
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_add_batch_favorites(authorized_client, db_session):
    """Массовое добавление в избранное."""
    # Arrange
    client, access_token = authorized_client

    # Создаем товары
    for pid in [801, 802, 803]:
        product = Product(product_id=pid, name=f"Product {pid}", brand="Test", subject="Test", entity="Test")
        db_session.add(product)
    await db_session.commit()

    # Act
    response = await client.post(
        "/user/favorites/batch",
        json={"product_ids": [801, 802, 803]},
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert "status" in data or "message" in data


@pytest.mark.asyncio
async def test_add_to_favorites_no_product_id_or_wb_article(authorized_client):
    """Добавление в избранное без product_id и wb_article (422 - validation error)."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.post("/user/favorites", json={})

    # Assert - Pydantic валидация возвращает 422
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_batch_favorites_empty_list(authorized_client):
    """Массовое добавление в избранное с пустым списком (сервер принимает)."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.post("/user/favorites/batch", json={"product_ids": []})

    # Assert - сервер принимает пустой список
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_update_profile_with_password(authorized_client):
    """Обновление профиля с паролем (проверка хеширования)."""
    # Arrange
    client, access_token = authorized_client

    # Act
    response = await client.patch("/user/profile", json={"password": "NewSecurePassword123"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    # Проверяем, что пароль не возвращается в ответе
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_link_telegram_already_linked(authorized_client, db_session):
    """Привязка Telegram когда уже привязан (сервер позволяет перепривязку)."""
    # Arrange
    client, access_token = authorized_client

    user = await db_session.execute(User.__table__.select().where(User.__table__.c.email == "user_api_test@example.com"))
    user_row = user.fetchone()

    # Сначала привязываем
    from src.services.UserService import link_telegram_by_bot
    await link_telegram_by_bot(555666, user_row.id, db_session)

    # Act - пытаемся привязать другой TG
    response = await client.post(f"/user/telegram/link?telegram_id=777888&user_id={user_row.id}")

    # Assert - сервер позволяет перепривязку
    assert response.status_code == 200
