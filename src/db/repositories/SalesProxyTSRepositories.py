from sqlalchemy import select, insert, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Sequence

from src.db.models import SalesProxyTS
from src.db.schemas.SalesProxyTS import SalesProxyTSCreate


async def create_sale_record(
        sale_in: SalesProxyTSCreate,
        session: AsyncSession
) -> SalesProxyTS:
    db_sale = SalesProxyTS(**sale_in.model_dump())
    session.add(db_sale)
    await session.commit()
    await session.refresh(db_sale)
    return db_sale


async def create_sales_bulk(
        sales_in: list[SalesProxyTSCreate],
        session: AsyncSession
):
    if not sales_in:
        return
    sales_data = [s.model_dump() for s in sales_in]

    await session.execute(insert(SalesProxyTS), sales_data)
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
    return result.scalar()


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
    return list(result.scalars().all())


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
