from sqlalchemy import select, func, and_, over
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.db.models import Product, PriceTS, SalesProxyTS, SocialTS, DeliveryTS, UserFavorite

async def check_user_favorite(session: AsyncSession, user_id: int, product_id: int) -> bool:
    stmt = select(UserFavorite).where(
        and_(
            UserFavorite.user_id == user_id,
            UserFavorite.product_id == product_id
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None

async def get_analytics_dataset(session: AsyncSession, user_id: int, days: int = 30):
    start_date = date.today() - timedelta(days=days)

    sales_agg = (
        select(
            PriceTS.product_id,
            func.avg(PriceTS.price_sale).label("avg_price"),
            func.sum(func.coalesce(SalesProxyTS.sales, 0)).label("total_sales"),
            func.stddev(SalesProxyTS.sales).label("sales_std"),
            func.avg(SalesProxyTS.sales).label("sales_avg"),
            # Считаем выручку сразу здесь
            func.sum(func.coalesce(SalesProxyTS.sales, 0) * PriceTS.price_sale).label("total_revenue")
        )
        .outerjoin(SalesProxyTS, and_(SalesProxyTS.product_id == PriceTS.product_id, SalesProxyTS.dt == PriceTS.dt))
        .where(PriceTS.dt >= start_date)
        .group_by(PriceTS.product_id)
    ).subquery("sales_agg")

    base_metrics = (
        select(
            Product.product_id,
            Product.subject,
            sales_agg.c.avg_price,
            sales_agg.c.total_sales,
            sales_agg.c.sales_std,
            sales_agg.c.sales_avg,
            func.avg(SocialTS.rating).label("avg_rating"),
            func.max(SocialTS.feedbacks).label("max_feedbacks"),
            func.avg(DeliveryTS.delivery_days).label("avg_delivery"),
            sales_agg.c.total_revenue
        )
        .join(UserFavorite, UserFavorite.product_id == Product.product_id)
        .join(sales_agg, Product.product_id == sales_agg.c.product_id) # Джоиним уже посчитанную выручку
        .outerjoin(SocialTS, and_(Product.product_id == SocialTS.product_id, SocialTS.dt >= start_date))
        .outerjoin(DeliveryTS, and_(Product.product_id == DeliveryTS.product_id, DeliveryTS.dt >= start_date))
        .where(UserFavorite.user_id == user_id)
        .group_by(
            Product.product_id,
            Product.subject,
            sales_agg.c.avg_price,
            sales_agg.c.total_sales,
            sales_agg.c.sales_std,
            sales_agg.c.sales_avg,
            sales_agg.c.total_revenue
        )
    ).subquery("base_metrics")

    final_stmt = select(
        base_metrics,
        (base_metrics.c.total_revenue /
         func.nullif(over(func.sum(base_metrics.c.total_revenue), partition_by=base_metrics.c.subject), 0)).label("category_share"),
        (over(func.sum(base_metrics.c.total_revenue), order_by=base_metrics.c.total_revenue.desc()) /
         func.nullif(over(func.sum(base_metrics.c.total_revenue)), 0)).label("cum_share_pct")
    )

    result = await session.execute(final_stmt)
    return result.all()

async def get_price_changes(session: AsyncSession, user_id: int):
    subq = (
        select(
            PriceTS.product_id,
            PriceTS.dt,
            PriceTS.price_sale.label("current_price"),
            func.lag(PriceTS.price_sale).over(
                partition_by=PriceTS.product_id,
                order_by=PriceTS.dt
            ).label("previous_price")
        )
        .join(UserFavorite, UserFavorite.product_id == PriceTS.product_id)
        .where(UserFavorite.user_id == user_id)
    ).subquery()

    stmt = (
        select(
            Product.name,
            subq.c.product_id,
            subq.c.dt,
            subq.c.current_price,
            subq.c.previous_price
        )
        .join(Product, Product.product_id == subq.c.product_id)
        .where(subq.c.previous_price.isnot(None))
        .where(subq.c.current_price != subq.c.previous_price)
        .order_by(subq.c.dt.desc())
    )

    result = await session.execute(stmt)
    return result.all()

async def get_product_history_raw(session: AsyncSession, product_id: int, days: int = 30):
    start_date = date.today() - timedelta(days=days)
    stmt = (
        select(
            PriceTS.dt,
            PriceTS.price_sale,
            func.coalesce(SalesProxyTS.sales, 0).label("sales")
        )
        .outerjoin(SalesProxyTS, and_(
            PriceTS.product_id == SalesProxyTS.product_id,
            PriceTS.dt == SalesProxyTS.dt
        ))
        .where(PriceTS.product_id == product_id)
        .where(PriceTS.dt >= start_date)
        .order_by(PriceTS.dt.asc())
    )
    result = await session.execute(stmt)
    return result.all()