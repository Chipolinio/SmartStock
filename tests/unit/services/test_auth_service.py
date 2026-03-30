"""
Юнит-тесты для AuthService (функциональный подход).

Тестируемые функции:
- registration() — создание пользователя, генерация токенов
- login() — проверка пароля, выдача токенов
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.AuthService import registration, login
from src.db.schemas.User import UserCreate, UserLogin


@pytest.mark.asyncio
async def test_registration_success(mocker):
    """Успешная регистрация пользователя."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    user_data = UserCreate(
        email="test@example.com",
        password="SecurePass123",
        role="user",
        is_pro=False,
        is_active=True
    )

    mock_new_user = MagicMock()
    mock_new_user.id = 1
    mock_new_user.user_id = None
    mock_new_user.role = "user"
    mock_new_user.is_pro = False
    mock_new_user.is_active = True

    def set_id(obj):
        obj.id = 1

    mock_session.refresh = AsyncMock(side_effect=set_id)

    mock_hash = mocker.patch(
        "src.services.AuthService.get_password_hash",
        return_value="hashed_password"
    )
    mock_create_token = mocker.patch(
        "src.services.AuthService.create_token",
        side_effect=lambda data, duration=1800: f"token_{data.get('sub')}"
    )
    
    # Мок User класса
    mock_user_class = mocker.patch("src.services.AuthService.User")
    mock_user_class.return_value = mock_new_user

    # Act
    token, refresh_token = await registration(user_data, mock_session)

    # Assert
    assert token == "token_1"
    assert refresh_token == "token_1"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_hash.assert_called_once_with("SecurePass123")
    assert mock_create_token.call_count == 2


@pytest.mark.asyncio
async def test_registration_duplicate_email(mocker):
    """Регистрация с дублирующимся email."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock(side_effect=IntegrityError(
        statement="",
        params=None,
        orig=MagicMock()
    ))
    mock_session.rollback = AsyncMock()

    user_data = UserCreate(
        email="existing@example.com",
        password="SecurePass123"
    )

    mocker.patch("src.services.AuthService.get_password_hash", return_value="hashed")
    mocker.patch("src.services.AuthService.User")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await registration(user_data, mock_session)

    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail
    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_registration_token_creation_error(mocker):
    """Ошибка при создании токена."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    user_data = UserCreate(
        email="test@example.com",
        password="SecurePass123"
    )

    mock_new_user = MagicMock()
    mock_new_user.id = 1

    def set_id(obj):
        obj.id = 1

    mock_session.refresh = AsyncMock(side_effect=set_id)

    mocker.patch("src.services.AuthService.get_password_hash", return_value="hashed")
    mocker.patch("src.services.AuthService.User", return_value=mock_new_user)
    mocker.patch(
        "src.services.AuthService.create_token",
        side_effect=Exception("Token error")
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await registration(user_data, mock_session)

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_registration_with_telegram_id(mocker):
    """Регистрация с привязанным Telegram ID."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    user_data = UserCreate(
        email="test@example.com",
        password="SecurePass123",
        user_id=123456789
    )

    mock_new_user = MagicMock()
    mock_new_user.id = 1
    mock_new_user.user_id = 123456789

    def set_id(obj):
        obj.id = 1

    mock_session.refresh = AsyncMock(side_effect=set_id)

    mocker.patch("src.services.AuthService.get_password_hash", return_value="hashed")
    mocker.patch("src.services.AuthService.User", return_value=mock_new_user)
    mocker.patch(
        "src.services.AuthService.create_token",
        side_effect=lambda data, duration=1800: f"token_{data.get('sub')}"
    )

    # Act
    token, refresh_token = await registration(user_data, mock_session)

    # Assert
    assert token == "token_1"
    assert mock_session.add.call_args[0][0].user_id == 123456789


@pytest.mark.asyncio
async def test_login_success_by_email(mocker):
    """Успешный вход по email."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    login_data = UserLogin(
        email="test@example.com",
        password="SecurePass123"
    )

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.user_id = 123456789
    mock_user.role = "user"
    mock_user.is_pro = False
    mock_user.is_active = True
    mock_user.password_hash = "hashed_password"

    mocker.patch(
        "src.services.AuthService.read_user_by_email",
        return_value=mock_user
    )
    mocker.patch(
        "src.services.AuthService.verify_password",
        return_value=True
    )
    mocker.patch(
        "src.services.AuthService.create_token",
        side_effect=lambda data, duration=1800: f"token_{data.get('sub')}"
    )

    # Act
    token, refresh_token = await login(login_data, mock_session)

    # Assert
    assert token == "token_1"
    assert refresh_token == "token_1"


@pytest.mark.asyncio
async def test_login_success_by_telegram_id(mocker):
    """Успешный вход по Telegram ID (цифровой email)."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    # Используем валидный email формат для Telegram ID
    login_data = UserLogin(
        email="123456789@test.com",
        password="SecurePass123"
    )

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.user_id = 123456789
    mock_user.is_active = True
    mock_user.password_hash = "hashed_password"

    # Сначала read_user_by_id возвращает None, потом read_user_by_email находит
    mocker.patch(
        "src.services.AuthService.read_user_by_id",
        return_value=None
    )
    mocker.patch(
        "src.services.AuthService.read_user_by_email",
        return_value=mock_user
    )
    mocker.patch(
        "src.services.AuthService.verify_password",
        return_value=True
    )
    mocker.patch(
        "src.services.AuthService.create_token",
        return_value="token_1"
    )

    # Act
    token, refresh_token = await login(login_data, mock_session)

    # Assert
    assert token == "token_1"


@pytest.mark.asyncio
async def test_login_user_not_found(mocker):
    """Вход с несуществующим пользователем."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    login_data = UserLogin(
        email="nonexistent@example.com",
        password="SecurePass123"
    )

    mocker.patch(
        "src.services.AuthService.read_user_by_email",
        return_value=None
    )
    mocker.patch(
        "src.services.AuthService.read_user_by_id",
        return_value=None
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await login(login_data, mock_session)

    assert exc_info.value.status_code == 401
    assert "Incorrect login or password" in exc_info.value.detail


@pytest.mark.asyncio
async def test_login_wrong_password(mocker):
    """Вход с неверным паролем."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    login_data = UserLogin(
        email="test@example.com",
        password="WrongPassword123"
    )

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.is_active = True
    mock_user.password_hash = "hashed_password"

    mocker.patch(
        "src.services.AuthService.read_user_by_email",
        return_value=mock_user
    )
    mocker.patch(
        "src.services.AuthService.verify_password",
        return_value=False
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await login(login_data, mock_session)

    assert exc_info.value.status_code == 401
    assert "Incorrect login or password" in exc_info.value.detail


@pytest.mark.asyncio
async def test_login_disabled_account(mocker):
    """Вход с неактивным аккаунтом."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    login_data = UserLogin(
        email="disabled@example.com",
        password="SecurePass123"
    )

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.is_active = False
    mock_user.password_hash = "hashed_password"

    mocker.patch(
        "src.services.AuthService.read_user_by_email",
        return_value=mock_user
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await login(login_data, mock_session)

    assert exc_info.value.status_code == 403
    assert "Account is disabled" in exc_info.value.detail


@pytest.mark.asyncio
async def test_login_database_error(mocker):
    """Вход с ошибкой базы данных."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    login_data = UserLogin(
        email="test@example.com",
        password="SecurePass123"
    )

    mocker.patch(
        "src.services.AuthService.read_user_by_email",
        side_effect=Exception("DB connection error")
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await login(login_data, mock_session)

    assert exc_info.value.status_code == 500
    assert "Internal server error" in exc_info.value.detail
