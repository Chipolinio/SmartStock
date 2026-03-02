import pytest
import numpy as np
from datetime import date, timedelta
from sqlalchemy import select
from src.db.models import (
    Product, PriceTS, StockTS, SocialTS,
    SalesProxyTS, ProductFeaturesDaily, PredictedSalesTS
)
from src.ml.engine import predict_sales_and_oos
from src.services.MLService import run_daily_forecast, run_model_training
from src.db.repositories.ProductFeaturesDailyRepositories import get_aggregated_features_data


@pytest.mark.asyncio
async def test_get_aggregated_features_logic(db_session):
    target_date = date(2026, 1, 21)

    db_session.add(Product(product_id=101, name="Coffee A", brand="X", subject="Coffee", entity="item"))

    db_session.add(PriceTS(product_id=101, dt=target_date, price_sale=1500.0, discount_pct=10.0))
    db_session.add(StockTS(product_id=101, dt=target_date, quantity=40))
    db_session.add(SocialTS(product_id=101, dt=target_date, rating=4.8, feedbacks=150))
    db_session.add(SalesProxyTS(product_id=101, dt=target_date - timedelta(days=1), sales=10, confidence=1.0))

    await db_session.flush()

    rows = await get_aggregated_features_data(db_session, target_date)

    assert len(rows) == 1
    assert float(rows[0].price_sale) == 1500.0
    assert rows[0].price_rank == 1


@pytest.mark.asyncio
async def test_run_daily_forecast_integration(db_session, mocker):
    target_date = date.today()

    db_session.add(Product(product_id=202, name="Tea B", brand="Y", subject="Tea", entity="item"))
    db_session.add(StockTS(product_id=202, dt=target_date, quantity=50))
    db_session.add(PriceTS(product_id=202, dt=target_date, price_sale=100.0, discount_pct=0.0))
    await db_session.flush()

    mocker.patch("src.ml.engine._engine.predict", return_value=np.array([12.5]))

    await run_daily_forecast(db_session, target_date)

    stmt = select(PredictedSalesTS).where(PredictedSalesTS.product_id == 202)
    result = await db_session.execute(stmt)
    prediction = result.scalar_one()

    assert float(prediction.predicted_sales) == 12.5


@pytest.mark.asyncio
async def test_run_model_training_db_loading(db_session, mocker):
    db_session.add(Product(product_id=303, name="Gadget C", brand="Z", subject="Tech", entity="item"))

    db_session.add(ProductFeaturesDaily(
        product_id=303,
        dt=date(2026, 1, 1),
        price=100.0,
        discount_pct=5.0,
        rating=4.5,
        feedbacks=10,
        stock_left=50,
        days_to_oos=10.0,
        price_rank_in_category=1,
        rating_rank_in_category=1,
        avg_sales_7d=5.0,
        avg_sales_14d=5.0
    ))
    await db_session.flush()

    mock_train = mocker.patch("src.ml.engine._engine.train", return_value=True)

    success = await run_model_training(db_session)

    assert success is True
    assert mock_train.called


@pytest.mark.asyncio
async def test_run_daily_forecast_idempotency(db_session, mocker):
    target_date = date(2026, 2, 1)
    pid = 555

    db_session.add(Product(product_id=pid, name="Test", brand="T", subject="S", entity="item"))
    db_session.add(StockTS(product_id=pid, dt=target_date, quantity=100))
    db_session.add(PriceTS(product_id=pid, dt=target_date, price_sale=100.0, discount_pct=0.0))
    await db_session.flush()

    mocker.patch("src.ml.engine._engine.predict", return_value=np.array([10.0]))

    await run_daily_forecast(db_session, target_date)
    await run_daily_forecast(db_session, target_date)

    stmt = select(PredictedSalesTS).where(PredictedSalesTS.product_id == pid, PredictedSalesTS.dt == target_date)
    result = await db_session.execute(stmt)
    predictions = result.scalars().all()

    assert len(predictions) == 1


def test_days_to_oos_calculation_logic(mocker):
    test_data = [
        {'product_id': 1, 'stock_left': 100, 'predicted_sales': 10.0},
        {'product_id': 2, 'stock_left': 50,  'predicted_sales': 0.0},
        {'product_id': 3, 'stock_left': 0,   'predicted_sales': 5.0},
        {'product_id': 4, 'stock_left': 10,  'predicted_sales': 0.0001}
    ]

    class Row:
        def __init__(self, data):
            self.d = data
        def _asdict(self):
            return {
                'product_id': self.d['product_id'],
                'quantity': self.d['stock_left'],
                'price_sale': 100.0 # Дефолт для теста
            }

    rows = [Row(d) for d in test_data]

    mocker.patch("src.ml.engine._engine.predict", return_value=np.array([10.0, 0.0, 5.0, 0.0001]))

    df_result = predict_sales_and_oos(rows)
    results = df_result.set_index('product_id')['days_to_oos'].to_dict()

    assert results[1] == 10.0
    assert results[2] == 999.0
    assert results[3] == 0.0
    assert results[4] == 999.0