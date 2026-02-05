from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
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

async def create_product_bulk(
    products_in: list[ProductCreate],
    session: AsyncSession
) -> list[Product]:
    if not products_in:
        return []

    products_data = [p.model_dump() for p in products_in]
    stmt = insert(Product).values(products_data)
    stmt = stmt.on_conflict_do_update(
        index_elements=['product_id'],
        set_={
            "name": stmt.excluded.name,
            "brand": stmt.excluded.brand,
            "subject": stmt.excluded.subject,
            "entity": stmt.excluded.entity,
        }
    ).returning(Product)

    result = await session.execute(stmt)
    return list(result.scalars().all())

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
        product_id: int,
        product_update: ProductUpdate,
        session: AsyncSession
) -> Product | None:
    stmt = select(Product).where(Product.product_id == product_id)
    result = await session.execute(stmt)
    db_product = result.scalar_one_or_none()

    if not db_product:
        return None

    update_data = product_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_product, key, value)

    session.add(db_product)

    return db_product


async def bulk_update_products(products_data: list[ProductUpdate], session: AsyncSession):
    if not products_data:
        return

    data = [p.model_dump(exclude_unset=True) for p in products_data]

    for item in data:
        if not item.get("entity"):
            item["entity"] = item.get("subject", "product")

        stmt = insert(Product).values(item)
        stmt = stmt.on_conflict_do_update(
            index_elements=['product_id'],
            set_={
                "name": stmt.excluded.name,
                "brand": stmt.excluded.brand,
                "subject": stmt.excluded.subject,
                "entity": stmt.excluded.entity
            }
        )
        await session.execute(stmt)

    await session.flush()

async def delete_product(
        product_id: int,
        session: AsyncSession
):
    stmt = delete(Product).where(Product.product_id == product_id)
    await session.execute(stmt)
    await session.commit()