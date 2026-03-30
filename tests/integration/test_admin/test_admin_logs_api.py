"""
Интеграционные тесты для Admin Logs API.

Тестируемые endpoints:
- GET /admin/logs — получение системных логов
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.SystemLog import SystemLog
from datetime import datetime


@pytest.fixture
async def test_logs(db_session: AsyncSession):
    """Фикстура: тестовые логи."""
    from src.db.models.SystemLog import TaskStatus
    
    logs = [
        SystemLog(
            task_name="scraper",
            status=TaskStatus.SUCCESS,
            processed_count=10,
            payload=None
        ),
        SystemLog(
            task_name="ml_training",
            status=TaskStatus.SUCCESS,
            processed_count=5,
            payload=None
        ),
        SystemLog(
            task_name="scraper",
            status=TaskStatus.ERROR,
            processed_count=0,
            payload=None
        ),
    ]
    for log in logs:
        db_session.add(log)
    await db_session.commit()
    return logs


@pytest.mark.asyncio
async def test_admin_get_logs_success(admin_client, test_logs):
    """Успешное получение логов."""
    # Arrange
    client, access_token = admin_client

    # Act
    response = await client.get("/admin/logs?limit=10")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10
    # Проверяем, что есть нужные поля
    for log in data:
        assert "task_name" in log
        assert "status" in log
        assert "processed_count" in log


@pytest.mark.asyncio
async def test_admin_get_logs_with_task_filter(admin_client, test_logs):
    """Получение логов с фильтром по task_name."""
    # Arrange
    client, access_token = admin_client

    # Act
    response = await client.get("/admin/logs?limit=10&task_name=scraper")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for log in data:
        assert log["task_name"] == "scraper"


@pytest.mark.asyncio
async def test_admin_get_logs_limit_validation(admin_client):
    """Валидация параметра limit (меньше 1)."""
    # Arrange
    client, access_token = admin_client

    # Act
    response = await client.get("/admin/logs?limit=0")

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_get_logs_limit_max_validation(admin_client):
    """Валидация параметра limit (больше 1000)."""
    # Arrange
    client, access_token = admin_client

    # Act
    response = await client.get("/admin/logs?limit=1001")

    # Assert
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_get_logs_default_limit(admin_client, test_logs):
    """Получение логов с limit по умолчанию (100)."""
    # Arrange
    client, access_token = admin_client

    # Act
    response = await client.get("/admin/logs")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_admin_get_logs_no_admin(regular_client):
    """Получение логов без admin прав (401)."""
    # Arrange
    client, access_token = regular_client

    # Act
    response = await client.get("/admin/logs")

    # Assert
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_get_logs_unauthorized(client: AsyncClient):
    """Получение логов без авторизации (401)."""
    # Act
    response = await client.get("/admin/logs")

    # Assert
    assert response.status_code == 401
