from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.schemas.Product import ProductCreate, ProductUpdate, ProductResponse
from src.db.repositories import ProductRepositories


async def create_product(product: ProductCreate, session: AsyncSession):
    try:
        product_from_db = await ProductRepositories.create_product(
            product_in = product,
            session = session
        )
        await session.commit()
        product_data = ProductResponse.model_validate(product_from_db)
        return product_data
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product already exists")


async def get_product_by_id(product_id: int, session: AsyncSession):
    product_from_db = await ProductRepositories.read_product(
        product_id = product_id,
        session = session
    )
    if not product_from_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    product_data = ProductResponse.model_validate(product_from_db)
    return product_data


async def get_products_filter(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        name: str | None = None,
        brand: str | None = None,
        subject: str | None = None,
        entity: str | None = None
):
    products_from_db = await ProductRepositories.read_products(
        session = session,
        skip = skip,
        limit = limit,
        name = name,
        brand = brand,
        subject = subject,
        entity = entity
    )
    product_data = [ProductResponse.model_validate(product) for product in products_from_db]
    return product_data

async def update_product(
        product_id: int,
        product: ProductUpdate,
        session: AsyncSession
):
    try:
        updated = await ProductRepositories.update_product(
            product_id=product_id,
            product_update=product,
            session=session
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Product not found")
        return ProductResponse.model_validate(updated)

    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Conflict: Check your data")

async def delete_product(product_id: int, session: AsyncSession):
    product_from_db = await ProductRepositories.read_product(
        product_id=product_id,
        session=session
    )
    if not product_from_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    await ProductRepositories.delete_product(
        product_id=product_id,
        session=session
    )
    return {"detail": "Product deleted successfully"}