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
    read_features_by_date,
    get_all_features_for_train,
    read_features_latest
)


async def run_daily_forecast(session: AsyncSession, target_date: date):
    raw_features = await read_features_by_date(session, target_date)

    if not raw_features:
        return None


    data_for_ml = []
    for f in raw_features:
        data_for_ml.append({
            "product_id": f.product_id,
            "price": float(f.price),
            "discount_pct": float(f.discount_pct or 0),
            "rating": float(f.rating or 0),
            "feedbacks": f.feedbacks or 0,
            "stock_left": f.stock_left,
            "price_rank_in_category": f.price_rank_in_category
        })


    df = predict_sales_and_oos(data_for_ml)

    if df.empty:
        return None

    if 'predicted_sales' not in df.columns:
        return None

    predictions = [
        PredictedSalesTSCreate(
            product_id=int(row['product_id']),
            dt=target_date,
            predicted_sales=float(row['predicted_sales']),
            model_version=MODEL_VERSION
        ) for _, row in df.iterrows()
    ]

    if predictions:
        res = await create_predict_sales_bulk(predictions, session)
        await session.commit()
        return res
    return None


async def run_model_training(session: AsyncSession):
    raw_history = await get_all_features_for_train(session)
    if not raw_history:
        return False

    data_list = []
    for row in raw_history:
        f = row.ProductFeaturesDaily
        data_list.append({
            'price': float(f.price),
            'discount_pct': float(f.discount_pct or 0),
            'rating': float(f.rating or 0),
            'feedbacks': f.feedbacks or 0,
            'stock_left': f.stock_left,
            'price_rank_in_category': f.price_rank_in_category,
            'target_sales': float(row.real_sales_next_day or 0)
        })

    df = pd.DataFrame(data_list)
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