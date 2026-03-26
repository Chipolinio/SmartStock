from sqlalchemy import select, delete, func, and_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.db.models.Product import Product
from src.db.models.SalesProxyTS import SalesProxyTS
from src.db.models.PriceTS import PriceTS
from src.db.models.SocialTS import SocialTS
from src.db.models.StockTS import StockTS
from src.db.schemas.Product import ProductCreate, ProductUpdate


async def get_by_article(
    wb_article: int,
    session: AsyncSession
) -> Product | None:
    """Получить товар по артикулу WB (product_id)."""
    stmt = select(Product).where(Product.product_id == wb_article)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_id_by_article(
    wb_article: int,
    session: AsyncSession
) -> int | None:
    """Получить внутренний product_id по артикулу WB."""
    stmt = select(Product.product_id).where(Product.product_id == wb_article)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_product(
    product_in: ProductCreate,
    session: AsyncSession
) -> Product:
    db_product = Product(**product_in.model_dump())
    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)
    return db_product


async def bulk_upsert_products(
    products_in: list[ProductCreate],
    session: AsyncSession
) -> list[Product]:
    """Массовое обновление/создание товаров (upsert)."""
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


# =============================================================================
# АНАЛИТИКА ТОВАРА (отдельные метрики)
# =============================================================================

async def get_product_current_price(
    product_id: int,
    session: AsyncSession
) -> float | None:
    """Получить текущую цену товара (последняя запись)."""
    stmt = (
        select(PriceTS.price_sale)
        .where(PriceTS.product_id == product_id)
        .order_by(PriceTS.dt.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_product_current_stock(
    product_id: int,
    session: AsyncSession
) -> int:
    """Получить текущий остаток товара (последняя запись)."""
    stmt = (
        select(StockTS.quantity)
        .where(StockTS.product_id == product_id)
        .order_by(StockTS.dt.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() or 0


async def get_product_avg_daily_sales(
    product_id: int,
    session: AsyncSession,
    days: int = 30
) -> float:
    """Получить средние продажи в день за период."""
    from datetime import date, timedelta
    start_date = date.today() - timedelta(days=days)
    
    stmt = (
        select(func.avg(SalesProxyTS.sales))
        .where(
            SalesProxyTS.product_id == product_id,
            SalesProxyTS.dt >= start_date
        )
    )
    result = await session.execute(stmt)
    return float(result.scalar_one_or_none() or 0)


async def get_product_social_metrics(
    product_id: int,
    session: AsyncSession
) -> tuple[float | None, int | None]:
    """Получить рейтинг и количество отзывов (последняя запись)."""
    stmt = (
        select(SocialTS.rating, SocialTS.feedbacks)
        .where(SocialTS.product_id == product_id)
        .order_by(SocialTS.dt.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    row = result.first()
    return (row.rating if row else None, row.feedbacks if row else None)


async def get_product_total_stats(
    product_id: int,
    session: AsyncSession
) -> tuple[int, float]:
    """Получить общую сумму продаж и выручку за всё время."""
    stmt = (
        select(
            func.sum(SalesProxyTS.sales).label("total_sales"),
            func.sum(SalesProxyTS.sales * PriceTS.price_sale).label("total_revenue")
        )
        .join(PriceTS, and_(
            PriceTS.product_id == SalesProxyTS.product_id,
            PriceTS.dt == SalesProxyTS.dt
        ))
        .where(SalesProxyTS.product_id == product_id)
    )
    result = await session.execute(stmt)
    row = result.first()
    return (
        row.total_sales if row and row.total_sales else 0,
        float(row.total_revenue) if row and row.total_revenue else 0.0
    )


async def get_product_detailed_stats(
    product_id: int,
    session: AsyncSession
) -> dict:
    """
    Получить полную статистику по товару для страницы аналитики.
    Собирает данные из отдельных методов.
    """
    price = await get_product_current_price(product_id, session)
    stock = await get_product_current_stock(product_id, session)
    avg_daily_sales = await get_product_avg_daily_sales(product_id, session)
    rating, reviews_count = await get_product_social_metrics(product_id, session)
    total_sales, total_revenue = await get_product_total_stats(product_id, session)
    
    days_to_oos = int(stock / avg_daily_sales) if avg_daily_sales > 0 else None
    
    return {
        "price": price,
        "stock": stock,
        "avg_daily_sales": avg_daily_sales,
        "days_to_oos": days_to_oos,
        "rating": rating,
        "reviews_count": reviews_count,
        "total_sales": total_sales,
        "total_revenue": total_revenue
    }
