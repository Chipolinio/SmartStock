from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Product


async def create_product(
        product: Product,
        session: AsyncSession
) -> Product:
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def read_product(
        product_id: int,
        session: AsyncSession
) -> Product | None:
    stmt = select(Product).where(Product.product_id == product_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def read_products(

    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    name: str | None = None,
    brand: str | None = None,
    subject: str | None = None,
    entity: str | None = None
) -> list[Product]:
    stmt = select(Product).offset(skip).limit(limit)

    if name:
        stmt.where(Product.name.ilike(f"%{name}%"))
    if brand:
        stmt = stmt.where(Product.brand == brand)
    if subject:
        stmt = stmt.where(Product.subject == subject)
    if entity:
        stmt = stmt.where(Product.entity == entity)

    result = await session.execute(stmt)
    return result.scalars().all()


async def update_product(
        product: Product,
        session: AsyncSession
):
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def delete_product(
        product_id: int,
        session: AsyncSession
):
    stmt = delete(Product).where(Product.product_id == product_id)
    await session.execute(stmt)
    await session.commit()