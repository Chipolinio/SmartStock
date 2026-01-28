from sqlalchemy import select, delete, desc
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Sequence

from src.db.models import SocialTS
from src.db.schemas.SocialTS import SocialTSCreate

async def create_social_record(social_in: SocialTSCreate, session: AsyncSession) -> SocialTS:
    db_social = SocialTS(**social_in.model_dump())
    session.add(db_social)
    return db_social

async def create_socials_bulk(
        social_in: list[SocialTSCreate],
        session: AsyncSession
) -> list[SocialTS]:
    if not social_in:
        return []
    social_data = [s.model_dump() for s in social_in]
    stmt = insert(SocialTS).values(social_data)
    stmt = stmt.on_conflict_do_nothing(index_elements=['product_id', 'dt']).returning(SocialTS)
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def read_social_latest(product_id: int, session: AsyncSession) -> SocialTS | None:
    stmt = select(SocialTS).where(SocialTS.product_id == product_id).order_by(desc(SocialTS.dt)).limit(1)
    result = await session.execute(stmt)
    return result.scalar()

async def read_socials_history(product_id: int, session: AsyncSession, limit: int = 30) -> Sequence[SocialTS]:
    stmt = select(SocialTS).where(SocialTS.product_id == product_id).order_by(desc(SocialTS.dt)).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def delete_social_by_date(product_id: int, dt: date, session: AsyncSession):
    stmt = delete(SocialTS).where(SocialTS.product_id == product_id).where(SocialTS.dt == dt)
    await session.execute(stmt)