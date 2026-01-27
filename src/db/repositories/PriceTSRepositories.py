from sqlalchemy import select, delete, desc
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Sequence

from src.db.models import PriceTS
from src.db.schemas.PriceTS import PriceTSCreate

async def create_price_record(price_in: PriceTSCreate, session: AsyncSession) -> PriceTS:
    db_price = PriceTS(**price_in.model_dump())
    session.add(db_price)
    return db_price

async def create_prices_bulk(prices_in: list[PriceTSCreate], session: AsyncSession):
    if not prices_in:
        return []
    prices_data = [p.model_dump() for p in prices_in]
    stmt = insert(PriceTS).values(prices_data)
    stmt = stmt.on_conflict_do_nothing(index_elements=['product_id', 'dt']).returning(PriceTS)
    result = await session.execute(stmt)
    return result.scalars().all()

async def read_price_latest(product_id: int, session: AsyncSession) -> PriceTS | None:
    stmt = select(PriceTS).where(PriceTS.product_id == product_id).order_by(desc(PriceTS.dt)).limit(1)
    result = await session.execute(stmt)
    return result.scalar()

async def read_prices_history(product_id: int, session: AsyncSession, limit: int = 30) -> Sequence[PriceTS]:
    stmt = select(PriceTS).where(PriceTS.product_id == product_id).order_by(desc(PriceTS.dt)).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def delete_price_by_date(product_id: int, dt: date, session: AsyncSession):
    stmt = delete(PriceTS).where(PriceTS.product_id == product_id).where(PriceTS.dt == dt)
    await session.execute(stmt)