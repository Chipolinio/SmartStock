"""
Юнит-тесты для bot handlers (функциональный подход).

Тестируемые обработчики:
- cmd_start() — команда /start
- cmd_link() — команда /link
- cmd_analytics() — команда /analytics
- cmd_forecast() — команда /forecast
- cmd_favorites() — команда /favorites
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message
from aiogram import Bot

from bot.handlers.start import cmd_start, cmd_link, process_link_command
from bot.handlers.analytics import cmd_analytics, cmd_forecast, cmd_favorites


@pytest.mark.asyncio
async def test_cmd_start_without_args(mocker):
    """Команда /start без аргументов."""
    # Arrange
    mock_from_user = MagicMock()
    mock_from_user.id = 123456

    mock_message = AsyncMock(spec=Message)
    mock_message.from_user = mock_from_user
    mock_message.answer = AsyncMock()

    mock_command = MagicMock()
    mock_command.args = None

    # Act
    await cmd_start(mock_message, mock_command)

    # Assert
    mock_message.answer.assert_called_once()
    call_text = mock_message.answer.call_args[0][0]
    assert "Добро пожаловать" in call_text or "Команды:" in call_text


@pytest.mark.asyncio
async def test_cmd_start_with_link_args(mocker):
    """Команда /start с аргументом для привязки."""
    # Arrange
    mock_from_user = MagicMock()
    mock_from_user.id = 123456

    mock_message = AsyncMock(spec=Message)
    mock_message.from_user = mock_from_user
    mock_message.answer = AsyncMock()

    mock_command = MagicMock()
    mock_command.args = "123"

    mock_process = mocker.patch("bot.handlers.start.process_link_command")

    # Act
    await cmd_start(mock_message, mock_command)

    # Assert
    mock_process.assert_called_once_with(mock_message, "123", 123456)


@pytest.mark.asyncio
async def test_cmd_link_without_args(mocker):
    """Команда /link без аргументов."""
    # Arrange
    mock_message = AsyncMock(spec=Message)
    mock_message.answer = AsyncMock()

    mock_command = MagicMock()
    mock_command.args = None

    # Act
    await cmd_link(mock_message, mock_command)

    # Assert
    mock_message.answer.assert_called_once()
    call_text = mock_message.answer.call_args[0][0]
    assert "не указан user_id" in call_text.lower() or "error" in call_text.lower()


@pytest.mark.asyncio
async def test_cmd_link_with_valid_args(mocker):
    """Команда /link с валидным аргументом."""
    # Arrange
    mock_from_user = MagicMock()
    mock_from_user.id = 123456

    mock_message = AsyncMock(spec=Message)
    mock_message.from_user = mock_from_user
    mock_message.answer = AsyncMock()

    mock_command = MagicMock()
    mock_command.args = "123"

    mock_process = mocker.patch("bot.handlers.start.process_link_command")

    # Act
    await cmd_link(mock_message, mock_command)

    # Assert
    mock_process.assert_called_once_with(mock_message, "123", 123456)


@pytest.mark.asyncio
async def test_process_link_command_invalid_user_id(mocker):
    """process_link_command с невалидным user_id."""
    # Arrange
    mock_message = AsyncMock(spec=Message)
    mock_message.answer = AsyncMock()

    # Act
    await process_link_command(mock_message, "invalid", 123456)

    # Assert
    mock_message.answer.assert_called_once()
    call_text = mock_message.answer.call_args[0][0]
    assert "числом" in call_text


@pytest.mark.asyncio
async def test_process_link_command_success(mocker):
    """process_link_command успешная привязка."""
    # Arrange
    mock_message = AsyncMock(spec=Message)
    mock_message.answer = AsyncMock()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={"message": "Telegram привязан"})

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mocker.patch("bot.handlers.start.httpx.AsyncClient", return_value=mock_client)

    # Act
    await process_link_command(mock_message, "123", 123456)

    # Assert
    mock_message.answer.assert_called()
    call_text = mock_message.answer.call_args[0][0]
    assert "привязан" in call_text.lower() or "success" in call_text.lower()


@pytest.mark.asyncio
async def test_process_link_command_error(mocker):
    """process_link_command с ошибкой."""
    # Arrange
    mock_message = AsyncMock(spec=Message)
    mock_message.answer = AsyncMock()

    mock_response = MagicMock()
    mock_response.status_code = 409
    mock_response.json = MagicMock(return_value={"detail": "Уже привязан"})

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mocker.patch("bot.handlers.start.httpx.AsyncClient", return_value=mock_client)

    # Act
    await process_link_command(mock_message, "123", 123456)

    # Assert
    mock_message.answer.assert_called()
    call_text = mock_message.answer.call_args[0][0]
    assert "ошибка" in call_text.lower() or "error" in call_text.lower()


@pytest.mark.asyncio
async def test_cmd_analytics_not_linked(mocker):
    """Команда /analytics для непривязанного пользователя."""
    # Arrange
    mock_from_user = MagicMock()
    mock_from_user.id = 123456

    mock_message = AsyncMock(spec=Message)
    mock_message.from_user = mock_from_user
    mock_message.answer = AsyncMock()

    mock_session = AsyncMock()

    # Мок пользователя не найден
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Act
    await cmd_analytics(mock_message, mock_session)

    # Assert
    mock_message.answer.assert_called_once()
    call_text = mock_message.answer.call_args[0][0]
    assert "не привязан" in call_text.lower() or "link" in call_text.lower()


@pytest.mark.asyncio
async def test_cmd_analytics_no_data(mocker):
    """Команда /analytics без данных."""
    # Arrange
    mock_from_user = MagicMock()
    mock_from_user.id = 123456

    mock_message = AsyncMock(spec=Message)
    mock_message.from_user = mock_from_user
    mock_message.answer = AsyncMock()

    mock_session = AsyncMock()

    mock_user = MagicMock()
    mock_user.id = 1

    mock_user_result = MagicMock()
    mock_user_result.scalar_one_or_none = MagicMock(return_value=mock_user)
    mock_session.execute = AsyncMock(return_value=mock_user_result)

    mocker.patch(
        "bot.handlers.analytics.get_abc_data",
        return_value=MagicMock(data=[])
    )

    # Act
    await cmd_analytics(mock_message, mock_session)

    # Assert
    mock_message.answer.assert_called()
    call_text = mock_message.answer.call_args[0][0]
    assert "нет" in call_text.lower() or "пуст" in call_text.lower()


@pytest.mark.asyncio
async def test_cmd_forecast_not_linked(mocker):
    """Команда /forecast для непривязанного пользователя."""
    # Arrange
    mock_from_user = MagicMock()
    mock_from_user.id = 123456

    mock_message = AsyncMock(spec=Message)
    mock_message.from_user = mock_from_user
    mock_message.answer = AsyncMock()

    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Act
    await cmd_forecast(mock_message, mock_session)

    # Assert
    mock_message.answer.assert_called_once()
    call_text = mock_message.answer.call_args[0][0]
    assert "не привязан" in call_text.lower() or "link" in call_text.lower()


@pytest.mark.asyncio
async def test_cmd_favorites_not_linked(mocker):
    """Команда /favorites для непривязанного пользователя."""
    # Arrange
    mock_from_user = MagicMock()
    mock_from_user.id = 123456

    mock_message = AsyncMock(spec=Message)
    mock_message.from_user = mock_from_user
    mock_message.answer = AsyncMock()

    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Act
    await cmd_favorites(mock_message, mock_session)

    # Assert
    mock_message.answer.assert_called_once()
    call_text = mock_message.answer.call_args[0][0]
    assert "не привязан" in call_text.lower() or "link" in call_text.lower()


@pytest.mark.asyncio
async def test_cmd_favorites_empty(mocker):
    """Команда /favorites с пустым списком."""
    # Arrange
    mock_from_user = MagicMock()
    mock_from_user.id = 123456

    mock_message = AsyncMock(spec=Message)
    mock_message.from_user = mock_from_user
    mock_message.answer = AsyncMock()

    mock_session = AsyncMock()

    mock_user = MagicMock()
    mock_user.id = 1

    mock_user_result = MagicMock()
    mock_user_result.scalar_one_or_none = MagicMock(return_value=mock_user)
    mock_session.execute = AsyncMock(return_value=mock_user_result)

    mocker.patch(
        "bot.handlers.analytics.read_user_favorites",
        return_value=[]
    )

    # Act
    await cmd_favorites(mock_message, mock_session)

    # Assert
    mock_message.answer.assert_called()
    call_text = mock_message.answer.call_args[0][0]
    assert "нет" in call_text.lower() or "пуст" in call_text.lower()
