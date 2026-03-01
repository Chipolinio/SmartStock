from datetime import date, timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.AnalyticsService import run_unified_analytics
from src.services.MLService import get_full_analysis
from src.db.schemas.Analytics import AnalyticsRequest, AnalyticsEntry
from src.db.repositories import UserFavoriteRepositories as FavRepo


async def get_favorites_analytics_summary(
        tg_id: int,
        session: AsyncSession
) -> List[AnalyticsEntry]:

    query = AnalyticsRequest(
        date_from=date.today() - timedelta(days=30),
        date_to=date.today(),
        dimensions=["product_id"],
        metrics=["revenue", "sales", "abc", "xyz", "score", "recommendation"],
        filters={}
    )

    return await run_unified_analytics(session, tg_id, query)


async def get_favorites_forecasts(
        tg_id: int,
        session: AsyncSession
) -> List[Dict[str, Any]]:
    fav_products = await FavRepo.read_user_favorites(tg_id, session)

    if not fav_products:
        return []

    forecasts = [
        await get_full_analysis(session, p.product_id)
        for p in fav_products
    ]

    return [f for f in forecasts if f is not None]