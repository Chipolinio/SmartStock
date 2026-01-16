from sqlalchemy import select, insert, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Sequence

from src.db.models import StockTS


async def create_stocks_bulk(
        prices_data: list[dict],
        session: AsyncSession
):
    if not prices_data:
        return

    await session.execute(insert(StockTS), prices_data)
    await session.commit()


async def read_stock_latest(
        product_id: int,
        session: AsyncSession
) -> StockTS | None:
    stmt = (
        select(StockTS)
        .where(StockTS.product_id == product_id)
        .order_by(desc(StockTS.dt))
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def read_stocks_history(
        product_id: int,
        session: AsyncSession,
        limit: int = 30
) -> Sequence[StockTS]:
    stmt = (
        select(StockTS)
        .where(StockTS.product_id == product_id)
        .order_by(desc(StockTS.dt))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_stock_by_date(
        product_id: int,
        dt: date,
        session: AsyncSession
):
    stmt = (
        delete(StockTS)
        .where(StockTS.product_id == product_id)
        .where(StockTS.dt == dt)
    )
    await session.execute(stmt)
    await session.commit()
