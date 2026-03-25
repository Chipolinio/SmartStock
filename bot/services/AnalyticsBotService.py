"""
Сервисы для бота (аналитика и прогнозы).
"""
from datetime import date, timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repositories.AnalyticsRepository import get_abc_data
from src.db.repositories.PredictedSalesTSRepositories import read_latest_prediction
from src.db.repositories.UserFavoriteRepositories import read_user_favorites


async def get_favorites_analytics_summary(
        user_id: int,
        session: AsyncSession
) -> dict:
    """
    Получить краткую сводку аналитики по избранным товарам.
    """
    abc_data = await get_abc_data(user_id, session, days=30)
    
    # Группируем по классам
    by_class = {"A": 0, "B": 0, "C": 0}
    total_revenue = 0
    
    for item in abc_data.data:
        by_class[item.abc_class] += 1
        total_revenue += item.total_revenue
    
    return {
        "total_products": len(abc_data.data),
        "class_a_count": by_class["A"],
        "class_b_count": by_class["B"],
        "class_c_count": by_class["C"],
        "total_revenue": total_revenue,
        "abc_data": abc_data.data[:5]  # Топ-5 для отображения
    }


async def get_favorites_forecasts(
        user_id: int,
        session: AsyncSession
) -> List[Dict[str, Any]]:
    """
    Получить прогнозы по избранным товарам.
    """
    fav_products = await read_user_favorites(user_id, session)

    if not fav_products:
        return []

    forecasts = []
    for p in fav_products[:5]:  # Первые 5 товаров
        prediction = await read_latest_prediction(p.product_id, session)
        if prediction:
            forecasts.append({
                "product_id": p.product_id,
                "product_name": p.name,
                "predicted_sales": float(prediction.predicted_sales),
                "model_version": prediction.model_version,
                "dt": prediction.dt
            })

    return forecasts