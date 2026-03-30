"""
Юнит-тесты для TaskSchedulerService (функциональный подход).

Тестируемые функции:
- run_daily_pipeline() — ежедневный пайплайн
- run_weekly_training() — еженедельное обучение
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date

from src.services.TaskSchedulerService import TaskSchedulerService


@pytest.fixture
def scheduler_service():
    """Фикстура: сервис планировщика."""
    return TaskSchedulerService()


@pytest.mark.asyncio
async def test_run_daily_pipeline_success(mocker, scheduler_service):
    """Успешное выполнение ежедневного пайплайна."""
    # Arrange
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.rollback = AsyncMock()

    mock_product = MagicMock()
    mock_product.product_id = 100

    mocker.patch(
        "src.services.TaskSchedulerService.AsyncSessionLocal",
        return_value=mock_session
    )
    mocker.patch(
        "src.services.TaskSchedulerService.ProductServiceModule.get_products_filter",
        return_value=[mock_product]
    )

    mock_data_pack = MagicMock()
    mock_scraper = MagicMock()
    mock_scraper.fetch_data = AsyncMock(return_value=mock_data_pack)
    mocker.patch(
        "src.services.TaskSchedulerService.WBScraper",
        return_value=mock_scraper
    )
    mocker.patch(
        "src.services.TaskSchedulerService.SalesServiceModule.process_full",
        return_value=True
    )
    mocker.patch(
        "src.services.TaskSchedulerService.fill_daily_dataset",
        return_value=None
    )
    mocker.patch(
        "src.services.TaskSchedulerService.run_daily_forecast",
        return_value=None
    )

    # Act
    await scheduler_service.run_daily_pipeline()

    # Assert
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_run_daily_pipeline_no_products(mocker, scheduler_service):
    """Пайплайн без товаров."""
    # Arrange
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    mocker.patch(
        "src.services.TaskSchedulerService.AsyncSessionLocal",
        return_value=mock_session
    )
    mocker.patch(
        "src.services.TaskSchedulerService.ProductServiceModule.get_products_filter",
        return_value=[]
    )

    # Act
    await scheduler_service.run_daily_pipeline()

    # Assert
    mock_session.commit.assert_not_called()
    mock_session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_run_daily_pipeline_scraper_error(mocker, scheduler_service):
    """Пайплайн с ошибкой скрапера."""
    # Arrange
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    mock_product = MagicMock()
    mock_product.product_id = 100

    mocker.patch(
        "src.services.TaskSchedulerService.AsyncSessionLocal",
        return_value=mock_session
    )
    mocker.patch(
        "src.services.TaskSchedulerService.ProductServiceModule.get_products_filter",
        return_value=[mock_product]
    )

    mock_scraper = MagicMock()
    mock_scraper.fetch_data = AsyncMock(side_effect=Exception("Scraper error"))
    mocker.patch(
        "src.services.TaskSchedulerService.WBScraper",
        return_value=mock_scraper
    )

    # Act
    await scheduler_service.run_daily_pipeline()

    # Assert
    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_run_daily_pipeline_process_error(mocker, scheduler_service):
    """Пайплайн с ошибкой обработки данных."""
    # Arrange
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    mock_product = MagicMock()
    mock_product.product_id = 100

    mocker.patch(
        "src.services.TaskSchedulerService.AsyncSessionLocal",
        return_value=mock_session
    )
    mocker.patch(
        "src.services.TaskSchedulerService.ProductServiceModule.get_products_filter",
        return_value=[mock_product]
    )

    mock_data_pack = MagicMock()
    mock_scraper = MagicMock()
    mock_scraper.fetch_data = AsyncMock(return_value=mock_data_pack)
    mocker.patch(
        "src.services.TaskSchedulerService.WBScraper",
        return_value=mock_scraper
    )
    mocker.patch(
        "src.services.TaskSchedulerService.SalesServiceModule.process_full",
        side_effect=Exception("Process error")
    )

    # Act
    await scheduler_service.run_daily_pipeline()

    # Assert
    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_run_weekly_training_success(mocker, scheduler_service):
    """Успешное еженедельное обучение модели."""
    # Arrange
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    mocker.patch(
        "src.services.TaskSchedulerService.AsyncSessionLocal",
        return_value=mock_session
    )
    mocker.patch(
        "src.services.TaskSchedulerService.run_model_training",
        return_value=True
    )

    # Act
    await scheduler_service.run_weekly_training()

    # Assert
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_run_weekly_training_no_data(mocker, scheduler_service):
    """Еженедельное обучение без данных."""
    # Arrange
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    mocker.patch(
        "src.services.TaskSchedulerService.AsyncSessionLocal",
        return_value=mock_session
    )
    mocker.patch(
        "src.services.TaskSchedulerService.run_model_training",
        return_value=False
    )

    # Act
    await scheduler_service.run_weekly_training()

    # Assert
    mock_session.commit.assert_not_called()
    mock_session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_run_weekly_training_error(mocker, scheduler_service):
    """Еженедельное обучение с ошибкой."""
    # Arrange
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    mocker.patch(
        "src.services.TaskSchedulerService.AsyncSessionLocal",
        return_value=mock_session
    )
    mocker.patch(
        "src.services.TaskSchedulerService.run_model_training",
        side_effect=Exception("Training error")
    )

    # Act
    await scheduler_service.run_weekly_training()

    # Assert
    mock_session.commit.assert_not_called()
    mock_session.rollback.assert_not_called()  # Ошибка логится, но не требует rollback


def test_scheduler_start(mocker, scheduler_service):
    """Тест запуска планировщика."""
    # Arrange
    mock_scheduler = MagicMock()
    mock_scheduler.add_job = MagicMock()
    mock_scheduler.start = MagicMock()

    scheduler_service.scheduler = mock_scheduler

    # Act
    scheduler_service.start()

    # Assert
    assert mock_scheduler.add_job.call_count == 2
    mock_scheduler.start.assert_called_once()


def test_scheduler_daily_pipeline_job(mocker, scheduler_service):
    """Тест: задача ежедневного пайплайна добавлена."""
    # Arrange
    mock_scheduler = MagicMock()

    scheduler_service.scheduler = mock_scheduler

    # Act
    scheduler_service.start()

    # Assert
    # Проверяем, что задача добавлена с правильным триггером
    add_job_calls = mock_scheduler.add_job.call_args_list
    assert len(add_job_calls) == 2

    # Первая задача - ежедневный пайплайн (hour=1, minute=0)
    first_call = add_job_calls[0]
    assert first_call[0][1] == "cron"
    assert first_call[1]["hour"] == 1
    assert first_call[1]["minute"] == 0


def test_scheduler_weekly_training_job(mocker, scheduler_service):
    """Тест: задача еженедельного обучения добавлена."""
    # Arrange
    mock_scheduler = MagicMock()

    scheduler_service.scheduler = mock_scheduler

    # Act
    scheduler_service.start()

    # Assert
    add_job_calls = mock_scheduler.add_job.call_args_list
    assert len(add_job_calls) == 2

    # Вторая задача - еженедельное обучение (day_of_week="sun", hour=3)
    second_call = add_job_calls[1]
    assert second_call[0][1] == "cron"
    assert second_call[1]["day_of_week"] == "sun"
    assert second_call[1]["hour"] == 3
