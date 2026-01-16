from sqlalchemy import select, insert, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Sequence

from src.db.models import SalesProxyTS


async def create_sales_bulk(
        prices_data: list[dict],
        session: AsyncSession
):
    if not prices_data:
        return

    await session.execute(insert(SalesProxyTS), prices_data)
    await session.commit()


async def read_sale_latest(
        product_id: int,
        session: AsyncSession
) -> SalesProxyTS | None:
    stmt = (
        select(SalesProxyTS)
        .where(SalesProxyTS.product_id == product_id)
        .order_by(desc(SalesProxyTS.dt))
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def read_sales_history(
        product_id: int,
        session: AsyncSession,
        limit: int = 30
) -> Sequence[SalesProxyTS]:
    stmt = (
        select(SalesProxyTS)
        .where(SalesProxyTS.product_id == product_id)
        .order_by(desc(SalesProxyTS.dt))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_sale_by_date(
        product_id: int,
        dt: date,
        session: AsyncSession
):
    stmt = (
        delete(SalesProxyTS)
        .where(SalesProxyTS.product_id == product_id)
        .where(SalesProxyTS.dt == dt)
    )
    await session.execute(stmt)
    await session.commit()
