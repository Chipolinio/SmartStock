from datetime import date, timedelta
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

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
from src.db.repositories.UserFavoriteRepositories import read_user_favorites, read_user_favorites_filtered
from src.db.models.Product import Product
from src.db.models.PredictedSalesTS import PredictedSalesTS
from src.db.models.PriceTS import PriceTS
from src.db.schemas.Forecast import (
    PredictionDetail,
    ProductForecast,
    ProductForecastsResponse,
    ForecastHistoryResponse,
    ForecastEntry,
    ForecastSummaryItem,
    ForecastSummaryResponse
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
    """Получить историю прогнозов для товара."""
    history = await read_predict_sales_history(product_id, session, limit)
    
    data = [
        ForecastEntry(
            dt=row.dt,
            predicted_sales=float(row.predicted_sales),
            model_version=row.model_version
        )
        for row in history
    ]
    
    return ForecastHistoryResponse(product_id=product_id, data=data)


async def get_product_forecasts(
    session: AsyncSession,
    user_id: int,
    days: int = 30,
    brand: str = None,
    subject: str = None
) -> ProductForecastsResponse:
    """Получить прогнозы по всем избранным товарам пользователя."""
    # Получаем избранные товары с фильтрами
    products = await read_user_favorites_filtered(user_id, session, brand=brand, subject=subject)

    if not products:
        return ProductForecastsResponse(data=[])

    start_date = date.today() - timedelta(days=days)
    data = []

    for product in products:
        # Последний прогноз
        latest_pred = await read_latest_prediction(product.product_id, session)
        
        # Текущие остатки для расчёта days_to_oos
        current_features = await read_features_latest(product.product_id, session)
        
        # Получаем текущую цену
        latest_price = await session.execute(
            select(PriceTS.price_sale)
            .where(PriceTS.product_id == product.product_id)
            .order_by(PriceTS.dt.desc())
            .limit(1)
        )
        price_row = latest_price.scalar_one_or_none()
        current_price = float(price_row) if price_row else 0.0
        
        # Рассчитываем days_to_oos
        days_to_oos = 999.0
        if latest_pred and current_features and latest_pred.predicted_sales > 0:
            days_to_oos = min(current_features.stock_left / float(latest_pred.predicted_sales), 999.0)
        
        # История прогнозов
        history = await read_predict_sales_history(product.product_id, session, limit=days)

        forecast_entry = ProductForecast(
            product_id=product.product_id,
            product_name=product.name,
            brand=product.brand,
            current_price=current_price,
            latest_prediction=PredictionDetail(
                sales_next_day=float(latest_pred.predicted_sales),
                days_until_out_of_stock=round(days_to_oos, 1),
                model_version=latest_pred.model_version,
                dt=latest_pred.dt
            ) if latest_pred else None,
            forecast_history=[
                ForecastEntry(
                    dt=row.dt,
                    predicted_sales=float(row.predicted_sales),
                    model_version=row.model_version
                )
                for row in history
            ]
        )
        data.append(forecast_entry)

    return ProductForecastsResponse(data=data)


async def get_forecast_summary(
    session: AsyncSession,
    user_id: int
) -> ForecastSummaryResponse:
    """Получить сводную статистику по прогнозам."""
    # Получаем избранные товары
    products = await read_user_favorites(user_id, session)
    
    if not products:
        return ForecastSummaryResponse(
            total_products=0,
            avg_predicted_sales=0.0,
            total_predicted_revenue=0.0,
            oos_risk_count=0,
            items=[]
        )
    
    items = []
    total_predicted_sales = 0.0
    total_revenue = 0.0
    oos_risk_count = 0
    
    for product in products:
        latest_pred = await read_latest_prediction(product.product_id, session)
        
        if latest_pred:
            predicted_sales = float(latest_pred.predicted_sales)
            total_predicted_sales += predicted_sales
            
            # Получаем цену для расчёта выручки
            latest_price = await session.execute(
                select(PriceTS.price_sale)
                .where(PriceTS.product_id == product.product_id)
                .order_by(PriceTS.dt.desc())
                .limit(1)
            )
            price_row = latest_price.scalar_one_or_none()
            price = float(price_row) if price_row else 0.0
            total_revenue += predicted_sales * price
            
            # Расчёт дней до OOS
            current_features = await read_features_latest(product.product_id, session)
            if current_features and predicted_sales > 0:
                days_to_oos = current_features.stock_left / predicted_sales
                is_oos_risk = days_to_oos < 7
                if is_oos_risk:
                    oos_risk_count += 1
            else:
                days_to_oos = None
                is_oos_risk = False
            
            items.append(
                ForecastSummaryItem(
                    product_id=product.product_id,
                    product_name=product.name,
                    predicted_sales=predicted_sales,
                    days_to_oos=round(days_to_oos, 1) if days_to_oos else None,
                    is_oos_risk=is_oos_risk
                )
            )
    
    total_products = len(items)
    avg_predicted_sales = total_predicted_sales / total_products if total_products > 0 else 0.0
    
    return ForecastSummaryResponse(
        total_products=total_products,
        avg_predicted_sales=avg_predicted_sales,
        total_predicted_revenue=total_revenue,
        oos_risk_count=oos_risk_count,
        items=items
    )