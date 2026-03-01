from datetime import date
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml.engine import predict_sales_and_oos, train_model, MODEL_VERSION
from src.db.schemas.PredictedSalesTS import PredictedSalesTSCreate
from src.db.repositories.PredictedSalesTSRepositories import (
    create_predict_sales_bulk,
    read_latest_prediction,
    read_predict_sales_history
)
from src.db.repositories.ProductFeaturesDailyRepositories import (
    get_aggregated_features_data,
    get_all_features_for_train,
    read_features_latest
)


async def run_daily_forecast(session: AsyncSession, target_date: date):
    raw_data = await get_aggregated_features_data(session, target_date)
    if not raw_data:
        return None

    df = predict_sales_and_oos(raw_data)

    predictions = [
        PredictedSalesTSCreate(
            product_id=row['product_id'],
            dt=target_date,
            predicted_sales=float(row['predicted_sales']),
            model_version=MODEL_VERSION
        ) for _, row in df.iterrows()
    ]

    if predictions:
        res = await create_predict_sales_bulk(predictions, session)
        await session.commit()
        return res


async def run_model_training(session: AsyncSession):
    raw_history = await get_all_features_for_train(session)
    if not raw_history:
        return False

    df = pd.DataFrame([
        {
            'price': float(r.price),
            'discount_pct': float(r.discount_pct or 0),
            'rating': float(r.rating or 0),
            'feedbacks': r.feedbacks or 0,
            'stock_left': r.stock_left,
            'price_rank_in_category': r.price_rank_in_category,
            'target_sales': float(r.avg_sales_7d or 0)
        } for r in raw_history
    ])

    return train_model(df)



async def get_product_forecast_summary(session: AsyncSession, product_id: int):
    prediction = await read_latest_prediction(product_id, session)
    if not prediction:
        return None
    return {
        "product_id": prediction.product_id,
        "forecast_date": prediction.dt,
        "predicted_sales": round(prediction.predicted_sales, 2),
        "model_version": prediction.model_version,
    }


async def get_full_analysis(session: AsyncSession, product_id: int):
    prediction = await read_latest_prediction(product_id, session)
    current_features = await read_features_latest(product_id, session)

    if not prediction or not current_features:
        return None

    stock = current_features.stock_left
    predicted = prediction.predicted_sales
    days_left = stock / predicted if predicted > 0 else 999

    return {
        "product_id": product_id,
        "current_stock": stock,
        "current_price": float(current_features.price),
        "prediction": {
            "sales_next_day": round(predicted, 2),
            "days_until_out_of_stock": round(days_left, 1),
            "model_version": prediction.model_version,
            "dt": prediction.dt
        },
        "alerts": {
            "is_low_stock": days_left < 7,
            "critical_oos": days_left < 3
        }
    }


async def get_forecast_history(session: AsyncSession, product_id: int, limit: int = 30):
    return await read_predict_sales_history(product_id, session, limit)