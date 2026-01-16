from sqlalchemy import select, insert, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Sequence

from src.db.models import PredictedSalesTS


async def create_predict_sales_bulk(
        prices_data: list[dict],
        session: AsyncSession
):
    if not prices_data:
        return

    await session.execute(insert(PredictedSalesTS), prices_data)
    await session.commit()


async def read_latest_prediction(
        product_id: int,
        session: AsyncSession,
        model_version: str | None = None
) -> PredictedSalesTS | None:
    stmt = (
        select(PredictedSalesTS)
        .where(PredictedSalesTS.product_id == product_id)
    )

    if model_version:
        stmt = stmt.where(PredictedSalesTS.model_version == model_version)

    stmt = stmt.order_by(desc(PredictedSalesTS.dt)).limit(1)

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def read_predict_sales_history(
        product_id: int,
        session: AsyncSession,
        limit: int = 30
) -> Sequence[PredictedSalesTS]:
    stmt = (
        select(PredictedSalesTS)
        .where(PredictedSalesTS.product_id == product_id)
        .order_by(desc(PredictedSalesTS.dt))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_predict_sale_by_date(
        product_id: int,
        dt: date,
        session: AsyncSession
):
    stmt = (
        delete(PredictedSalesTS)
        .where(PredictedSalesTS.product_id == product_id)
        .where(PredictedSalesTS.dt == dt)
    )
    await session.execute(stmt)
    await session.commit()
