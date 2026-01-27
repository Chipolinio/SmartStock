from sqlalchemy import select, delete, desc
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Sequence

from src.db.models import DeliveryTS
from src.db.schemas.DeliveryTS import DeliveryTSCreate

async def create_delivery_record(delivery_in: DeliveryTSCreate, session: AsyncSession) -> DeliveryTS:
    db_delivery = DeliveryTS(**delivery_in.model_dump())
    session.add(db_delivery)
    return db_delivery

async def create_deliveries_bulk(deliveries_in: list[DeliveryTSCreate], session: AsyncSession):
    if not deliveries_in:
        return []
    deliveries_data = [d.model_dump() for d in deliveries_in]
    stmt = insert(DeliveryTS).values(deliveries_data)
    stmt = stmt.on_conflict_do_nothing(index_elements=['product_id', 'dt']).returning(DeliveryTS)
    result = await session.execute(stmt)
    return result.scalars().all()

async def read_latest_delivery(product_id: int, session: AsyncSession) -> DeliveryTS | None:
    stmt = select(DeliveryTS).where(DeliveryTS.product_id == product_id).order_by(desc(DeliveryTS.dt)).limit(1)
    result = await session.execute(stmt)
    return result.scalar()

async def read_delivery_history(product_id: int, session: AsyncSession, limit: int = 30) -> Sequence[DeliveryTS]:
    stmt = select(DeliveryTS).where(DeliveryTS.product_id == product_id).order_by(desc(DeliveryTS.dt)).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def delete_delivery_by_date(product_id: int, dt: date, session: AsyncSession):
    stmt = delete(DeliveryTS).where(DeliveryTS.product_id == product_id).where(DeliveryTS.dt == dt)
    await session.execute(stmt)