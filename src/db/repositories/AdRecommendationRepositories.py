from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from src.db.models.AdRecommendation import AdRecommendation
from src.db.schemas.AdRecommendation import AdRecommendationCreate


async def create_ad_recommendation(
    data: AdRecommendationCreate,
    session: AsyncSession
) -> AdRecommendation:
    db_record = AdRecommendation(**data.model_dump())
    session.add(db_record)
    return db_record


async def create_ad_recommendations_bulk(
    data_list: list[AdRecommendationCreate],
    session: AsyncSession
) -> list[AdRecommendation]:
    if not data_list:
        return []
    records = [AdRecommendation(**d.model_dump()) for d in data_list]
    session.add_all(records)
    return records


async def read_recommendations_by_user(
    user_id: int,
    session: AsyncSession,
    limit: int = 50,
    product_id: int | None = None,
    category: str | None = None,
) -> Sequence[AdRecommendation]:
    stmt = (
        select(AdRecommendation)
        .where(AdRecommendation.user_id == user_id)
    )
    if product_id is not None:
        stmt = stmt.where(AdRecommendation.product_id == product_id)
    if category is not None:
        stmt = stmt.where(AdRecommendation.category == category)
    stmt = stmt.order_by(desc(AdRecommendation.created_at)).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_recommendations_by_user(
    user_id: int,
    session: AsyncSession,
) -> int:
    stmt = (
        select(func.count())
        .select_from(AdRecommendation)
        .where(AdRecommendation.user_id == user_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one()
