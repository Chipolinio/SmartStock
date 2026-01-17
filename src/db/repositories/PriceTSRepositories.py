from sqlalchemy import select, insert, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Sequence

from src.db.models import PriceTs
from src.db.schemas.PriceTS import PriceTSCreate


async def create_price_record(
        price_in: PriceTSCreate,
        session: AsyncSession
) -> PriceTs:
    db_price = PriceTs(**price_in.model_dump())
    session.add(db_price)
    await session.commit()
    await session.refresh(db_price)
    return db_price


async def create_prices_bulk(
        prices_in: list[PriceTSCreate],
        session: AsyncSession
):
    if not prices_in:
        return
    prices_data = [p.model_dump() for p in prices_in]

    await session.execute(insert(PriceTs), prices_data)
    await session.commit()
    

async def read_price_latest(
        product_id: int,
        session: AsyncSession
) -> PriceTs | None:
    stmt = (
        select(PriceTs)
        .where(PriceTs.product_id == product_id)
        .order_by(desc(PriceTs.dt))
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar()


async def read_prices_history(
        product_id: int,
        session: AsyncSession,
        limit: int = 30
) -> Sequence[PriceTs]:
    stmt = (
        select(PriceTs)
        .where(PriceTs.product_id == product_id)
        .order_by(desc(PriceTs.dt))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_price_by_date(
        product_id: int,
        dt: date,
        session: AsyncSession
):
    stmt = (
        delete(PriceTs)
        .where(PriceTs.product_id == product_id)
        .where(PriceTs.dt == dt)
    )
    await session.execute(stmt)
    await session.commit()
