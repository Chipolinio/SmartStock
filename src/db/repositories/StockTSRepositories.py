from sqlalchemy import select, delete, desc, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Sequence

from src.db.models.StockTS import StockTS
from src.db.schemas.StockTS import StockTSCreate


async def create_stock_record(
        stock_in: StockTSCreate,
        session: AsyncSession
) -> StockTS:
    db_stock = StockTS(**stock_in.model_dump())
    session.add(db_stock)
    return db_stock

async def create_stocks_bulk(
        stock_in: list[StockTSCreate],
        session: AsyncSession
) -> list[StockTS]:
    if not stock_in:
        return []

    stocks_data = [s.model_dump() for s in stock_in]

    stmt = insert(StockTS).values(stocks_data)

    stmt = stmt.on_conflict_do_nothing(
        index_elements=['product_id', 'dt']
    ).returning(StockTS)

    result = await session.execute(stmt)
    return list(result.scalars().all())


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
    return result.scalar()


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
    return list(result.scalars().all())


async def read_latest_stocks_for_products(
        product_ids: list[int],
        session: AsyncSession
) -> list[StockTS]:
    subq = (
        select(
            StockTS,
            func.row_number().over(
                partition_by=StockTS.product_id,
                order_by=desc(StockTS.dt)
            ).label("rn")
        )
        .where(StockTS.product_id.in_(product_ids))
        .subquery()
    )
    stmt = select(StockTS).from_statement(
        select(subq).where(subq.c.rn == 1)
    )

    result = await session.execute(stmt)
    return list(result.scalars().all())

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
