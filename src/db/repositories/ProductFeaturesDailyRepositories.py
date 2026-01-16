from sqlalchemy import select, insert, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Sequence

from src.db.models import ProductFeaturesDaily


async def create_features_daily_bulk(
    features_data: list[dict],
    session: AsyncSession
):
    if not features_data:
        return
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
    return result.scalar_one_or_none()


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
    return result.scalars().all()