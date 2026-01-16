from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Product
from src.db.schemas.Product import ProductCreate, ProductUpdate


async def create_product(
    product_in: ProductCreate,
    session: AsyncSession
) -> Product:
    db_product = Product(**product_in.model_dump())
    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)
    return db_product


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
        stmt = stmt.where(Product.name.ilike(f"%{name}%"))
    if brand:
        stmt = stmt.where(Product.brand == brand)
    if subject:
        stmt = stmt.where(Product.subject == subject)
    if entity:
        stmt = stmt.where(Product.entity == entity)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_product(
        db_id: int,
        product_update: ProductUpdate,
        session: AsyncSession
) -> Product | None:
    stmt = select(Product).where(Product.id == db_id)
    result = await session.execute(stmt)
    db_product = result.scalar_one_or_none()

    if not db_product:
        return None

    update_data = product_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_product, key, value)

    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)
    return db_product

async def delete_product(
        product_id: int,
        session: AsyncSession
):
    stmt = delete(Product).where(Product.product_id == product_id)
    await session.execute(stmt)
    await session.commit()