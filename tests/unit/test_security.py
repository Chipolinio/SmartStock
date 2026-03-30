"""
Юнит-тесты для security модуля (функциональный подход).

Тестируемые функции:
- get_password_hash() — хеширование пароля
- verify_password() — проверка пароля
- create_token() — создание JWT токена
- decode_token() — декодирование токена
- set_auth_token() — установка cookie
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from starlette.responses import Response

from src.utils.security import (
    get_password_hash,
    verify_password,
    create_token,
    decode_token,
    set_auth_token,
)


def test_get_password_hash():
    """Тест хеширования пароля."""
    # Arrange
    password = "SecurePass123"

    # Act
    hashed = get_password_hash(password)

    # Assert
    assert hashed is not None
    assert len(hashed) > 0
    assert hashed != password  # Хеш не должен совпадать с паролем
    assert isinstance(hashed, str)


def test_get_password_hash_different_salts():
    """Тест: разные хеши для одного пароля (из-за соли)."""
    # Arrange
    password = "SecurePass123"

    # Act
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    # Assert
    assert hash1 != hash2  # Хеши должны отличаться из-за разной соли


def test_verify_password_success():
    """Тест успешной проверки пароля."""
    # Arrange
    password = "SecurePass123"
    hashed = get_password_hash(password)

    # Act
    result = verify_password(password, hashed)

    # Assert
    assert result is True


def test_verify_password_failure():
    """Тест неудачной проверки пароля."""
    # Arrange
    password = "SecurePass123"
    wrong_password = "WrongPassword"
    hashed = get_password_hash(password)

    # Act
    result = verify_password(wrong_password, hashed)

    # Assert
    assert result is False


def test_verify_password_empty_strings():
    """Тест проверки пустых строк."""
    # Arrange
    hashed = get_password_hash("password")

    # Act
    result = verify_password("", hashed)

    # Assert
    assert result is False


def test_create_token_success():
    """Тест успешного создания токена."""
    # Arrange
    data = {"sub": "123", "role": "user"}
    duration = 3600  # 1 час

    # Act
    token = create_token(data, duration)

    # Assert
    assert token is not None
    assert len(token) > 0
    assert isinstance(token, str)


def test_create_token_contains_exp():
    """Тест: токен содержит срок действия."""
    # Arrange
    data = {"sub": "123"}
    duration = 3600

    # Act
    token = create_token(data, duration)

    # Assert
    decoded = decode_token(token)
    assert "exp" in decoded
    exp_timestamp = decoded["exp"]
    exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    now = datetime.now(timezone.utc)

    # Срок действия должен быть примерно через duration секунд
    assert exp_datetime > now
    assert exp_datetime <= now + timedelta(seconds=duration + 10)


def test_create_token_preserves_data():
    """Тест: токен сохраняет исходные данные."""
    # Arrange
    data = {"sub": "123", "role": "admin", "is_pro": True}

    # Act
    token = create_token(data)
    decoded = decode_token(token)

    # Assert
    assert decoded["sub"] == "123"
    assert decoded["role"] == "admin"
    assert decoded["is_pro"] is True


def test_create_token_default_duration():
    """Тест: токен с длительностью по умолчанию (1800 секунд)."""
    # Arrange
    data = {"sub": "123"}

    # Act
    token = create_token(data)  # Без указания duration
    decoded = decode_token(token)

    # Assert
    exp_timestamp = decoded["exp"]
    exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    now = datetime.now(timezone.utc)

    # Длительность по умолчанию 1800 секунд (30 минут)
    assert exp_datetime <= now + timedelta(seconds=1810)


def test_decode_token_valid():
    """Тест декодирования валидного токена."""
    # Arrange
    data = {"sub": "123", "role": "user"}
    token = create_token(data)

    # Act
    decoded = decode_token(token)

    # Assert
    assert decoded["sub"] == "123"
    assert decoded["role"] == "user"


def test_decode_token_expired():
    """Тест декодирования просроченного токена."""
    # Arrange
    data = {"sub": "123"}

    # Создаем токен с отрицательной длительностью (просроченный)
    with patch("src.utils.security.datetime") as mock_datetime:
        # Фиксируем текущее время
        fixed_now = datetime(2026, 3, 29, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        token = create_token(data, duration=-100)  # Токен уже просрочен

    # Assert - должен выбросить исключение
    with pytest.raises(Exception):
        decode_token(token)


def test_decode_token_invalid():
    """Тест декодирования невалидного токена."""
    # Arrange
    invalid_token = "invalid.token.here"

    # Act & Assert
    with pytest.raises(Exception):
        decode_token(invalid_token)


def test_decode_token_tampered():
    """Тест декодирования подделанного токена."""
    # Arrange
    data = {"sub": "123", "role": "user"}
    token = create_token(data)

    # Меняем полезную нагрузку токена (это нарушит подпись)
    import base64
    import json

    parts = token.split(".")
    if len(parts) == 3:
        # Декодируем payload и меняем данные
        payload_data = base64.urlsafe_b64decode(parts[1] + "==")
        payload = json.loads(payload_data)
        payload["sub"] = "999"  # Меняем user_id

        # Кодируем обратно (но подпись останется старой)
        new_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        tampered_token = f"{parts[0]}.{new_payload}.{parts[2]}"

        # Act & Assert
        with pytest.raises(Exception):
            decode_token(tampered_token)
    else:
        # Если токен не в формате JWT, пропускаем тест
        pytest.skip("Token format not suitable for tampering test")


def test_set_auth_token_success():
    """Тест успешной установки cookie с токеном."""
    # Arrange
    response = Response()
    token = "test_token_123"
    key = "access_token"
    max_age = 1800

    # Act
    set_auth_token(response, token, key, max_age)

    # Assert
    # Проверяем, что cookie установлен
    cookies = response.headers.getlist("set-cookie")
    assert len(cookies) > 0

    cookie_str = cookies[0]
    assert "access_token" in cookie_str
    assert "test_token_123" in cookie_str
    assert "httponly" in cookie_str.lower() or "HttpOnly" in cookie_str
    assert "samesite" in cookie_str.lower() or "SameSite" in cookie_str


def test_set_auth_token_default_max_age():
    """Тест установки cookie с max_age по умолчанию."""
    # Arrange
    response = Response()
    token = "test_token"
    key = "refresh_token"

    # Act
    set_auth_token(response, token, key)  # Без указания max_age

    # Assert
    cookies = response.headers.getlist("set-cookie")
    assert len(cookies) > 0

    cookie_str = cookies[0]
    # Max-age по умолчанию 1800 секунд
    assert "refresh_token" in cookie_str


def test_set_auth_token_path():
    """Тест: cookie установлен с правильным путем."""
    # Arrange
    response = Response()
    token = "test_token"
    key = "access_token"

    # Act
    set_auth_token(response, token, key)

    # Assert
    cookies = response.headers.getlist("set-cookie")
    cookie_str = cookies[0]
    assert "path=/" in cookie_str.lower()
