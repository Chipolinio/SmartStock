import pytest
import numpy as np
from unittest.mock import AsyncMock
from datetime import date
from src.services.MLService import run_daily_forecast, run_model_training

class MockRow:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def _asdict(self):
        return self.__dict__

@pytest.mark.asyncio
async def test_run_daily_forecast_success(mocker):
    mock_raw = [
        MockRow(
            product_id=101, price_sale=500.0, discount_pct=0.0,
            rating=4.8, feedbacks=50, quantity=10,
            avg_7d=2.0, avg_14d=2.0, price_rank=1, rating_rank=1
        )
    ]

    mocker.patch(
        "src.services.MLService.get_aggregated_features_data",
        new_callable=AsyncMock,
        return_value=mock_raw
    )

    mock_save = mocker.patch(
        "src.services.MLService.create_predict_sales_bulk",
        new_callable=AsyncMock
    )

    mocker.patch("src.ml.engine._engine.predict", return_value=np.array([5.0]))

    session = AsyncMock()
    await run_daily_forecast(session, date.today())

    assert mock_save.called
    args, _ = mock_save.call_args
    assert args[0][0].predicted_sales == 5.0

@pytest.mark.asyncio
async def test_run_model_training_no_data(mocker):
    mocker.patch(
        "src.services.MLService.get_all_features_for_train",
        new_callable=AsyncMock,
        return_value=[]
    )

    result = await run_model_training(AsyncMock())
    assert result is False