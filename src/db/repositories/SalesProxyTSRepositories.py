from sqlalchemy import select, delete, desc, func, and_, Float
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from typing import Sequence

from src.db.models.SalesProxyTS import SalesProxyTS
from src.db.models.StockTS import StockTS
from src.db.schemas.SalesProxyTS import SalesProxyTSCreate


async def create_sale_record(
        sale_in: SalesProxyTSCreate,
        session: AsyncSession
) -> SalesProxyTS:
    db_sale = SalesProxyTS(**sale_in.model_dump())
    session.add(db_sale)
    return db_sale


async def create_sales_bulk(
        sales_in: list[SalesProxyTSCreate],
        session: AsyncSession
) -> list[SalesProxyTS]:
    if not sales_in:
        return []

    sales_data = [s.model_dump() for s in sales_in]

    stmt = insert(SalesProxyTS).values(sales_data)

    stmt = stmt.on_conflict_do_nothing(
        index_elements=['product_id', 'dt']
    ).returning(SalesProxyTS)

    result = await session.execute(stmt)
    return list(result.scalars().all())



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


async def calculate_velocity_with_oos(
        product_id: int,
        days: int,
        session: AsyncSession
) -> float:
    start_date = date.today() - timedelta(days=days)

    stmt = (
        select(
            (func.sum(SalesProxyTS.sales) / func.cast(func.count(SalesProxyTS.dt), Float)))
        .join(
            StockTS,
            and_(
                StockTS.product_id == SalesProxyTS.product_id,
                StockTS.dt == SalesProxyTS.dt)
        )
        .where(
            SalesProxyTS.product_id == product_id,
            StockTS.quantity > 0,
            SalesProxyTS.dt >= start_date )
    )

    result = await session.execute(stmt)
    velocity = result.scalar()
    return float(velocity) if velocity else 0.0