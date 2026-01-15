from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.models import Product, User, PriceTS
from src import schema

# Products
async def get_product_by_external_id(db: AsyncSession, product_id: int):
    result = await db.execute(select(Product).where(Product.product_id == product_id))
    return result.scalars().first()

async def create_product(db: AsyncSession, product: schema.ProductCreate):
    db_product = Product(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product

# Prices (TimeSeries)
async def add_price_entry(db: AsyncSession, price_data: schema.PriceCreate):
    db_price = PriceTS(**price_data.model_dump())
    db.add(db_price)
    await db.commit()
    return db_price

# Users
async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()