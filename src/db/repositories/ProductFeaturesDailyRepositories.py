from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, case
from sqlalchemy.dialects.postgresql import insert
from datetime import date, timedelta
from typing import Sequence

from src.db.models import (
    Product, PriceTS, SocialTS, StockTS,
    SalesProxyTS, ProductFeaturesDaily
)
from src.db.schemas.ProductFeaturesDaily import ProductFeaturesDailyCreate


async def create_features_daily_record(
        features_in: ProductFeaturesDailyCreate,
        session: AsyncSession
) -> ProductFeaturesDaily:
    db_features = ProductFeaturesDaily(**features_in.model_dump())
    session.add(db_features)
    await session.commit()
    await session.refresh(db_features)
    return db_features


async def create_features_daily_bulk(features_in: list[ProductFeaturesDailyCreate], session: AsyncSession):
    if not features_in:
        return

    features_data = [f.model_dump() for f in features_in]
    stmt = insert(ProductFeaturesDaily).values(features_data)

    # Если запись (product_id + dt) уже есть — обновляем все поля
    stmt = stmt.on_conflict_do_update(
        index_elements=['product_id', 'dt'],
        set_={
            "price": stmt.excluded.price,
            "discount_pct": stmt.excluded.discount_pct,
            "rating": stmt.excluded.rating,
            "feedbacks": stmt.excluded.feedbacks,
            "avg_sales_7d": stmt.excluded.avg_sales_7d,
            "avg_sales_14d": stmt.excluded.avg_sales_14d,
            "stock_left": stmt.excluded.stock_left,
            "days_to_oos": stmt.excluded.days_to_oos,
            "price_rank_in_category": stmt.excluded.price_rank_in_category,
            "rating_rank_in_category": stmt.excluded.rating_rank_in_category,
        }
    )

    await session.execute(stmt)


async def read_features_latest(
    product_id: int,
    session: AsyncSession
) -> ProductFeaturesDaily | None:
    stmt = (
        select(ProductFeaturesDaily)
        .where(ProductFeaturesDaily.product_id == product_id)
        .order_by(desc(ProductFeaturesDaily.dt))
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar()


async def read_features_history(
    product_id: int,
    session: AsyncSession,
    limit: int = 30
) -> Sequence[ProductFeaturesDaily]:
    stmt = (
        select(ProductFeaturesDaily)
        .where(ProductFeaturesDaily.product_id == product_id)
        .order_by(desc(ProductFeaturesDaily.dt))
        .limit(limit)
    )

    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_aggregated_features_data(session: AsyncSession, target_date: date):

    def latest_record(model):
        return (
            select(model)
            .distinct(model.product_id)
            .order_by(model.product_id, desc(model.dt))
            .subquery()
        )

    p_latest = latest_record(PriceTS)
    s_latest = latest_record(StockTS)
    soc_latest = latest_record(SocialTS)

    start_date_14 = target_date - timedelta(days=14)
    sales_agg = (
        select(
            SalesProxyTS.product_id,
            func.avg(case((SalesProxyTS.dt >= target_date - timedelta(days=7), SalesProxyTS.sales), else_=None)).label("avg_7d"),
            func.avg(SalesProxyTS.sales).label("avg_14d")
        )
        .where(SalesProxyTS.dt >= start_date_14)
        .group_by(SalesProxyTS.product_id)
        .subquery()
    )

    stmt = (
        select(
            Product.product_id,
            p_latest.c.price_sale,
            p_latest.c.discount_pct,
            soc_latest.c.rating,
            soc_latest.c.feedbacks,
            s_latest.c.quantity,
            sales_agg.c.avg_7d,
            sales_agg.c.avg_14d,
            func.rank().over(
                partition_by=Product.subject,
                order_by=p_latest.c.price_sale
            ).label("price_rank"),
            func.rank().over(
                partition_by=Product.subject,
                order_by=desc(soc_latest.c.rating)
            ).label("rating_rank")
        )
        .outerjoin(p_latest, Product.product_id == p_latest.c.product_id)
        .outerjoin(s_latest, Product.product_id == s_latest.c.product_id)
        .outerjoin(soc_latest, Product.product_id == soc_latest.c.product_id)
        .outerjoin(sales_agg, Product.product_id == sales_agg.c.product_id)
    )

    result = await session.execute(stmt)
    return result.all()