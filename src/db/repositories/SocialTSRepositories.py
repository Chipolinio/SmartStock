from sqlalchemy import select, insert, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Sequence

from src.db.models import SocialTS


async def create_socials_bulk(
        prices_data: list[dict],
        session: AsyncSession
):
    if not prices_data:
        return

    await session.execute(insert(SocialTS), prices_data)
    await session.commit()


async def read_social_latest(
        product_id: int,
        session: AsyncSession
) -> SocialTS | None:
    stmt = (
        select(SocialTS)
        .where(SocialTS.product_id == product_id)
        .order_by(desc(SocialTS.dt))
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def read_socials_history(
        product_id: int,
        session: AsyncSession,
        limit: int = 30
) -> Sequence[SocialTS]:
    stmt = (
        select(SocialTS)
        .where(SocialTS.product_id == product_id)
        .order_by(desc(SocialTS.dt))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_social_by_date(
        product_id: int,
        dt: date,
        session: AsyncSession
):
    stmt = (
        delete(SocialTS)
        .where(SocialTS.product_id == product_id)
        .where(SocialTS.dt == dt)
    )
    await session.execute(stmt)
    await session.commit()
