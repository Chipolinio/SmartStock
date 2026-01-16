from sqlalchemy import select, insert, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Sequence

from src.db.models import PriceTs


async def create_prices_bulk(
        prices_data: list[dict],
        session: AsyncSession
):
    if not prices_data:
        return

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
    return result.scalar_one_or_none()


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
    return result.scalars().all()


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
