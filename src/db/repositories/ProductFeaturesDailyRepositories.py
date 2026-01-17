from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete, desc
from datetime import date
from typing import Sequence

from src.db.models import ProductFeaturesDaily
from src.db.schemas.ProductFeaturesDaily import ProductFeaturesDailyCreate


async def create_features_daily_record(
        features_in: ProductFeaturesDailyCreate,
        session: AsyncSession
) -> ProductFeaturesDaily:
    db_features = ProductFeaturesDaily(**features_in.model_dump())
    session.add(db_features)
    await session.commit()
    await session.refresh(db_features)
    return db_features


async def create_features_daily_bulk(
        features_in: list[ProductFeaturesDailyCreate],
        session: AsyncSession
):
    if not features_in:
        return
    features_data = [f.model_dump() for f in features_in]

    await session.execute(insert(ProductFeaturesDaily), features_data)
    await session.commit()


async def read_features_latest(
    product_id: int,
    session: AsyncSession
) -> ProductFeaturesDaily | None:
    stmt = (
        select(ProductFeaturesDaily)
        .where(ProductFeaturesDaily.product_id == product_id)
        .order_by(desc(ProductFeaturesDaily.dt))
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar()


async def read_features_history(
    product_id: int,
    session: AsyncSession,
    limit: int = 30
) -> Sequence[ProductFeaturesDaily]:
    stmt = (
        select(ProductFeaturesDaily)
        .where(ProductFeaturesDaily.product_id == product_id)
        .order_by(desc(ProductFeaturesDaily.dt))
        .limit(limit)
    )

    result = await session.execute(stmt)
    return list(result.scalars().all())