import pytest
from datetime import date
from src.ml.engine import SalesMLProvider
from src.services.MLService import MLForecastService
from src.db.database import AsyncSessionLocal


@pytest.mark.asyncio
async def test_run():
    provider = SalesMLProvider()
    service = MLForecastService(provider)

    async with AsyncSessionLocal() as session:
        await service.run_daily_forecast(session, date.today())
        print("🚀 Тестовый запуск завершен!")