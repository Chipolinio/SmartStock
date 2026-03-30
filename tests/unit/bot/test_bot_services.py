"""
Юнит-тесты для bot services (функциональный подход).

Тестируемые функции:
- get_user_profile() — профиль пользователя
- get_user_favorites() — избранные товары
- get_favorites_analytics_summary() — аналитика избранных
- get_favorites_forecasts() — прогнозы избранных
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.services.UserBotService import get_user_profile, get_user_favorites
from bot.services.AnalyticsBotService import (
    get_favorites_analytics_summary,
    get_favorites_forecasts
)


@pytest.mark.asyncio
async def test_get_user_profile_success(mocker):
    """Успешное получение профиля пользователя."""
    # Arrange
    mock_session = AsyncMock()

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.is_pro = True

    mocker.patch(
        "bot.services.UserBotService.UserRepo.read_user_by_id",
        return_value=mock_user
    )

    # Act
    result = await get_user_profile(tg_id=123456, session=mock_session)

    # Assert
    assert result == mock_user
    assert result.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_profile_not_found(mocker):
    """Получение профиля несуществующего пользователя."""
    # Arrange
    mock_session = AsyncMock()

    mocker.patch(
        "bot.services.UserBotService.UserRepo.read_user_by_id",
        return_value=None
    )

    # Act
    result = await get_user_profile(tg_id=999, session=mock_session)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_user_favorites_success(mocker):
    """Успешное получение избранных товаров."""
    # Arrange
    mock_session = AsyncMock()

    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.name = "Test Product"

    mocker.patch(
        "bot.services.UserBotService.FavRepo.read_user_favorites",
        return_value=[mock_product]
    )

    # Act
    result = await get_user_favorites(tg_id=1, session=mock_session)

    # Assert
    assert len(result) == 1
    assert result[0].name == "Test Product"


@pytest.mark.asyncio
async def test_get_user_favorites_empty(mocker):
    """Получение пустого списка избранного."""
    # Arrange
    mock_session = AsyncMock()

    mocker.patch(
        "bot.services.UserBotService.FavRepo.read_user_favorites",
        return_value=[]
    )

    # Act
    result = await get_user_favorites(tg_id=1, session=mock_session)

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_favorites_analytics_summary_success(mocker):
    """Успешное получение сводки аналитики."""
    # Arrange
    mock_session = AsyncMock()

    # Мок ABC данных
    mock_item_a = MagicMock()
    mock_item_a.abc_class = "A"
    mock_item_a.total_revenue = 100000.0
    mock_item_a.product_name = "Product A"

    mock_item_b = MagicMock()
    mock_item_b.abc_class = "B"
    mock_item_b.total_revenue = 50000.0
    mock_item_b.product_name = "Product B"

    mock_item_c = MagicMock()
    mock_item_c.abc_class = "C"
    mock_item_c.total_revenue = 10000.0
    mock_item_c.product_name = "Product C"

    mock_abc_data = MagicMock()
    mock_abc_data.data = [mock_item_a, mock_item_b, mock_item_c]

    mocker.patch(
        "bot.services.AnalyticsBotService.get_abc_data",
        return_value=mock_abc_data
    )

    # Act
    result = await get_favorites_analytics_summary(user_id=1, session=mock_session)

    # Assert
    assert result["total_products"] == 3
    assert result["class_a_count"] == 1
    assert result["class_b_count"] == 1
    assert result["class_c_count"] == 1
    assert result["total_revenue"] == 160000.0
    assert len(result["abc_data"]) == 3


@pytest.mark.asyncio
async def test_get_favorites_analytics_summary_empty(mocker):
    """Получение сводки аналитики для пустого списка."""
    # Arrange
    mock_session = AsyncMock()

    mock_abc_data = MagicMock()
    mock_abc_data.data = []

    mocker.patch(
        "bot.services.AnalyticsBotService.get_abc_data",
        return_value=mock_abc_data
    )

    # Act
    result = await get_favorites_analytics_summary(user_id=1, session=mock_session)

    # Assert
    assert result["total_products"] == 0
    assert result["class_a_count"] == 0
    assert result["class_b_count"] == 0
    assert result["class_c_count"] == 0
    assert result["total_revenue"] == 0.0


@pytest.mark.asyncio
async def test_get_favorites_forecasts_success(mocker):
    """Успешное получение прогнозов."""
    # Arrange
    mock_session = AsyncMock()

    mock_product = MagicMock()
    mock_product.product_id = 100
    mock_product.name = "Test Product"

    mock_prediction = MagicMock()
    mock_prediction.predicted_sales = 10.5
    mock_prediction.model_version = "catboost_v1"
    mock_prediction.dt = "2026-03-29"

    mocker.patch(
        "bot.services.AnalyticsBotService.read_user_favorites",
        return_value=[mock_product]
    )
    mocker.patch(
        "bot.services.AnalyticsBotService.read_latest_prediction",
        return_value=mock_prediction
    )

    # Act
    result = await get_favorites_forecasts(user_id=1, session=mock_session)

    # Assert
    assert len(result) == 1
    assert result[0]["product_id"] == 100
    assert result[0]["product_name"] == "Test Product"
    assert result[0]["predicted_sales"] == 10.5


@pytest.mark.asyncio
async def test_get_favorites_forecasts_no_prediction(mocker):
    """Получение прогнозов без данных прогноза."""
    # Arrange
    mock_session = AsyncMock()

    mock_product = MagicMock()
    mock_product.product_id = 100
    mock_product.name = "Test Product"

    mocker.patch(
        "bot.services.AnalyticsBotService.read_user_favorites",
        return_value=[mock_product]
    )
    mocker.patch(
        "bot.services.AnalyticsBotService.read_latest_prediction",
        return_value=None
    )

    # Act
    result = await get_favorites_forecasts(user_id=1, session=mock_session)

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_favorites_forecasts_empty_favorites(mocker):
    """Получение прогнозов для пустого списка избранного."""
    # Arrange
    mock_session = AsyncMock()

    mocker.patch(
        "bot.services.AnalyticsBotService.read_user_favorites",
        return_value=[]
    )

    # Act
    result = await get_favorites_forecasts(user_id=1, session=mock_session)

    # Assert
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_favorites_forecasts_multiple_products(mocker):
    """Получение прогнозов для нескольких товаров."""
    # Arrange
    mock_session = AsyncMock()

    mock_product1 = MagicMock()
    mock_product1.product_id = 100
    mock_product1.name = "Product 1"

    mock_product2 = MagicMock()
    mock_product2.product_id = 200
    mock_product2.name = "Product 2"

    mock_prediction1 = MagicMock()
    mock_prediction1.predicted_sales = 10.5
    mock_prediction1.model_version = "catboost_v1"
    mock_prediction1.dt = "2026-03-29"

    mock_prediction2 = MagicMock()
    mock_prediction2.predicted_sales = 5.0
    mock_prediction2.model_version = "catboost_v1"
    mock_prediction2.dt = "2026-03-29"

    mocker.patch(
        "bot.services.AnalyticsBotService.read_user_favorites",
        return_value=[mock_product1, mock_product2]
    )
    mocker.patch(
        "bot.services.AnalyticsBotService.read_latest_prediction",
        side_effect=[mock_prediction1, mock_prediction2]
    )

    # Act
    result = await get_favorites_forecasts(user_id=1, session=mock_session)

    # Assert
    assert len(result) == 2
    assert result[0]["product_id"] == 100
    assert result[0]["predicted_sales"] == 10.5
    assert result[1]["product_id"] == 200
    assert result[1]["predicted_sales"] == 5.0
