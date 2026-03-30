"""
Интеграционные тесты для SystemLogRepository.

Тестируемые методы:
- log_event
- get_logs
- get_log_by_id
- get_recent_logs
- get_system_logs
"""

import pytest
import json
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from src.db.models.SystemLog import SystemLog, TaskStatus
from src.db.repositories.SystemLogRepository import (
    log_event,
    get_logs,
    get_log_by_id,
    get_recent_logs,
    get_system_logs,
)


@pytest.fixture
async def sample_logs(db_session: AsyncSession):
    """Фикстура: набор тестовых логов."""
    logs = []
    
    # Создаём логи для разных задач
    for i in range(10):
        # SUCCESS логи для scraper
        log_scraper_success = SystemLog(
            task_name="scraper",
            status=TaskStatus.SUCCESS,
            processed_count=100 + i * 10,
            payload=json.dumps({"items_scraped": 100 + i * 10}),
            created_at=datetime.now() - timedelta(hours=i)
        )
        db_session.add(log_scraper_success)
        logs.append(log_scraper_success)
        
        # ERROR логи для scraper (каждый 3-й)
        if i % 3 == 0:
            log_scraper_error = SystemLog(
                task_name="scraper",
                status=TaskStatus.ERROR,
                processed_count=i * 5,
                payload=json.dumps({"error": f"Error on iteration {i}"}),
                created_at=datetime.now() - timedelta(hours=i, minutes=30)
            )
            db_session.add(log_scraper_error)
            logs.append(log_scraper_error)
        
        # Логи для ml_pipeline
        log_ml = SystemLog(
            task_name="ml_pipeline",
            status=TaskStatus.SUCCESS if i % 2 == 0 else TaskStatus.ERROR,
            processed_count=50 + i * 5,
            payload=json.dumps({"model_accuracy": 0.85 + i * 0.01}),
            created_at=datetime.now() - timedelta(hours=i, minutes=15)
        )
        db_session.add(log_ml)
        logs.append(log_ml)
    
    await db_session.commit()
    return logs


# =============================================================================
# log_event тесты
# =============================================================================

@pytest.mark.asyncio
async def test_log_event_success(db_session: AsyncSession):
    """Создание лога успешного выполнения."""
    # Act
    result = await log_event(
        session=db_session,
        task_name="test_task",
        status=TaskStatus.SUCCESS,
        processed_count=100,
        payload=json.dumps({"items": 100})
    )

    # Assert
    assert result is not None
    assert result.task_name == "test_task"
    assert result.status == TaskStatus.SUCCESS
    assert result.processed_count == 100
    assert result.id is not None


@pytest.mark.asyncio
async def test_log_event_error(db_session: AsyncSession):
    """Создание лога ошибки."""
    # Act
    result = await log_event(
        session=db_session,
        task_name="failing_task",
        status=TaskStatus.ERROR,
        processed_count=50,
        payload=json.dumps({"error": "Connection timeout", "traceback": "stack trace"})
    )

    # Assert
    assert result is not None
    assert result.task_name == "failing_task"
    assert result.status == TaskStatus.ERROR


@pytest.mark.asyncio
async def test_log_event_minimal(db_session: AsyncSession):
    """Создание лога с минимальными данными."""
    # Act
    result = await log_event(
        session=db_session,
        task_name="simple_task",
        status=TaskStatus.SUCCESS
    )

    # Assert
    assert result is not None
    assert result.task_name == "simple_task"
    assert result.status == TaskStatus.SUCCESS
    assert result.processed_count == 0
    assert result.payload is None


# =============================================================================
# get_logs тесты
# =============================================================================

@pytest.mark.asyncio
async def test_get_logs_all(db_session: AsyncSession, sample_logs):
    """Получение всех логов."""
    # Act
    result = await get_logs(db_session, limit=100)

    # Assert
    assert len(result) > 0
    # Проверяем сортировку по убыванию created_at
    for i in range(len(result) - 1):
        assert result[i].created_at >= result[i + 1].created_at


@pytest.mark.asyncio
async def test_get_logs_filtered_by_task(db_session: AsyncSession, sample_logs):
    """Получение логов с фильтром по задаче."""
    # Act
    result = await get_logs(db_session, task_name="scraper", limit=100)

    # Assert
    assert len(result) > 0
    assert all(log.task_name == "scraper" for log in result)


@pytest.mark.asyncio
async def test_get_logs_filtered_by_status(db_session: AsyncSession, sample_logs):
    """Получение логов с фильтром по статусу."""
    # Act
    result = await get_logs(db_session, status=TaskStatus.ERROR, limit=100)

    # Assert
    assert len(result) > 0
    assert all(log.status == TaskStatus.ERROR for log in result)


@pytest.mark.asyncio
async def test_get_logs_filtered_by_task_and_status(
    db_session: AsyncSession,
    sample_logs
):
    """Получение логов с фильтрами по задаче и статусу."""
    # Act
    result = await get_logs(
        db_session,
        task_name="ml_pipeline",
        status=TaskStatus.ERROR,
        limit=100
    )

    # Assert
    assert len(result) > 0
    assert all(log.task_name == "ml_pipeline" for log in result)
    assert all(log.status == TaskStatus.ERROR for log in result)


@pytest.mark.asyncio
async def test_get_logs_pagination(db_session: AsyncSession, sample_logs):
    """Пагинация логов."""
    # Act
    page1 = await get_logs(db_session, limit=5, offset=0)
    page2 = await get_logs(db_session, limit=5, offset=5)

    # Assert
    assert len(page1) == 5
    assert len(page2) == 5
    # Проверяем что страницы не пересекаются
    page1_ids = {log.id for log in page1}
    page2_ids = {log.id for log in page2}
    assert len(page1_ids & page2_ids) == 0


@pytest.mark.asyncio
async def test_get_logs_empty(db_session: AsyncSession):
    """Получение логов при отсутствии данных."""
    # Act
    result = await get_logs(db_session, limit=10)

    # Assert
    assert len(result) == 0


# =============================================================================
# get_log_by_id тесты
# =============================================================================

@pytest.mark.asyncio
async def test_get_log_by_id(db_session: AsyncSession, sample_logs):
    """Получение лога по ID."""
    # Arrange
    log_id = sample_logs[0].id

    # Act
    result = await get_log_by_id(db_session, log_id)

    # Assert
    assert result is not None
    assert result.id == log_id


@pytest.mark.asyncio
async def test_get_log_by_id_not_found(db_session: AsyncSession):
    """Получение несуществующего лога по ID."""
    # Act
    result = await get_log_by_id(db_session, 99999)

    # Assert
    assert result is None


# =============================================================================
# get_recent_logs тесты
# =============================================================================

@pytest.mark.asyncio
async def test_get_recent_logs(db_session: AsyncSession, sample_logs):
    """Получение последних логов для задачи."""
    # Act
    result = await get_recent_logs(db_session, task_name="scraper", limit=5)

    # Assert
    assert len(result) <= 5
    assert all(log.task_name == "scraper" for log in result)
    # Проверяем сортировку по убыванию created_at
    for i in range(len(result) - 1):
        assert result[i].created_at >= result[i + 1].created_at


@pytest.mark.asyncio
async def test_get_recent_logs_all_statuses(db_session: AsyncSession, sample_logs):
    """Получение последних логов включая все статусы."""
    # Act
    result = await get_recent_logs(db_session, task_name="scraper", limit=20)

    # Assert
    # Должны быть как SUCCESS так и ERROR логи
    statuses = {log.status for log in result}
    assert TaskStatus.SUCCESS in statuses
    assert TaskStatus.ERROR in statuses


@pytest.mark.asyncio
async def test_get_recent_logs_empty(db_session: AsyncSession):
    """Получение последних логов для несуществующей задачи."""
    # Act
    result = await get_recent_logs(db_session, task_name="nonexistent_task", limit=10)

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_recent_logs_limit_zero(db_session: AsyncSession, sample_logs):
    """Получение последних логов с limit=0."""
    # Act
    result = await get_recent_logs(db_session, task_name="scraper", limit=0)

    # Assert
    assert len(result) == 0


# =============================================================================
# get_system_logs тесты
# =============================================================================

@pytest.mark.asyncio
async def test_get_system_logs_all(db_session: AsyncSession, sample_logs):
    """Получение системных логов без фильтра."""
    # Act
    result = await get_system_logs(db_session, limit=100)

    # Assert
    assert len(result) > 0
    # Проверяем сортировку по убыванию created_at
    for i in range(len(result) - 1):
        assert result[i].created_at >= result[i + 1].created_at


@pytest.mark.asyncio
async def test_get_system_logs_filtered(db_session: AsyncSession, sample_logs):
    """Получение системных логов с фильтром по задаче."""
    # Act
    result = await get_system_logs(db_session, limit=100, task_name="ml_pipeline")

    # Assert
    assert len(result) > 0
    assert all(log.task_name == "ml_pipeline" for log in result)


@pytest.mark.asyncio
async def test_get_system_logs_pagination(db_session: AsyncSession, sample_logs):
    """Пагинация системных логов."""
    # Act - get_system_logs не поддерживает offset, используем limit
    page1 = await get_system_logs(db_session, limit=5)
    page2 = await get_system_logs(db_session, limit=5, task_name="scraper")

    # Assert
    assert len(page1) == 5
    assert len(page2) <= 5


@pytest.mark.asyncio
async def test_get_system_logs_empty(db_session: AsyncSession):
    """Получение системных логов при отсутствии данных."""
    # Act
    result = await get_system_logs(db_session, limit=10)

    # Assert
    assert len(result) == 0


# =============================================================================
# TaskStatus enum тесты
# =============================================================================

@pytest.mark.asyncio
async def test_task_status_enum(db_session: AsyncSession):
    """Тест enum TaskStatus."""
    # Assert
    assert TaskStatus.SUCCESS.value == "SUCCESS"
    assert TaskStatus.ERROR.value == "ERROR"


@pytest.mark.asyncio
async def test_log_both_statuses(db_session: AsyncSession):
    """Создание логов с обоими статусами."""
    # Act
    success_log = await log_event(
        session=db_session,
        task_name="status_test",
        status=TaskStatus.SUCCESS,
        processed_count=100
    )
    
    error_log = await log_event(
        session=db_session,
        task_name="status_test",
        status=TaskStatus.ERROR,
        processed_count=50,
        payload=json.dumps({"error": "Test error"})
    )

    # Assert
    assert success_log.status == TaskStatus.SUCCESS
    assert error_log.status == TaskStatus.ERROR
