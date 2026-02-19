from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.repositories.ProductFeaturesDailyRepositories  import (
    get_aggregated_features_data,
    create_features_daily_bulk
)
from src.db.schemas.ProductFeaturesDaily import ProductFeaturesDailyCreate


async def fill_daily_dataset(session: AsyncSession, target_date: date = None):
    dt = target_date or date.today()

    raw_data = await get_aggregated_features_data(session, dt)

    features_to_create = []
    for row in raw_data:
        v7 = float(row.avg_7d or 0)
        stock = row.quantity or 0
        days_oos = 999.0
        if v7 > 0:
            days_oos = min(float(stock / v7), 999.0)

        features_to_create.append(
            ProductFeaturesDailyCreate(
                product_id=row.product_id,
                dt=dt,
                price=float(row.price_sale or 0),
                discount_pct=float(row.discount_pct or 0),
                rating=float(row.rating or 0),
                feedbacks=row.feedbacks or 0,
                avg_sales_7d=v7,
                avg_sales_14d=float(row.avg_14d or 0),
                stock_left=stock,
                days_to_oos=days_oos,
                price_rank_in_category=row.price_rank,
                rating_rank_in_category=row.rating_rank
            )
        )

    if features_to_create:
        await create_features_daily_bulk(features_to_create, session)