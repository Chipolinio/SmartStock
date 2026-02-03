from sqlalchemy import select, func, and_, over
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.db.models import Product, PriceTS, SalesProxyTS, SocialTS, DeliveryTS, UserFavorite

async def get_analytics_dataset(session: AsyncSession, user_id: int, days: int = 30):
    start_date = date.today() - timedelta(days=days)

    base_agg = (
        select(
            PriceTS.product_id,
            PriceTS.dt,
            func.avg(PriceTS.price_sale).label("daily_price"),
            func.sum(func.coalesce(SalesProxyTS.sales, 0)).label("daily_sales"),
            # Выручка за конкретный день
            (func.sum(func.coalesce(SalesProxyTS.sales, 0)) * func.avg(PriceTS.price_sale)).label("daily_revenue")
        )
        .outerjoin(SalesProxyTS, and_(SalesProxyTS.product_id == PriceTS.product_id, SalesProxyTS.dt == PriceTS.dt))
        .where(PriceTS.dt >= start_date)
        .group_by(PriceTS.product_id, PriceTS.dt)
    ).subquery("base_agg")

    base_metrics = (
        select(
            Product.product_id,
            Product.subject,
            func.avg(base_agg.c.daily_price).label("avg_price"),
            func.sum(base_agg.c.daily_sales).label("total_sales"),
            func.stddev(base_agg.c.daily_sales).label("sales_std"),
            func.avg(base_agg.c.daily_sales).label("sales_avg"),
            func.avg(SocialTS.rating).label("avg_rating"),
            func.max(SocialTS.feedbacks).label("max_feedbacks"),
            func.avg(DeliveryTS.delivery_days).label("avg_delivery"),
            func.sum(base_agg.c.daily_revenue).label("total_revenue")
        )
        .join(UserFavorite, UserFavorite.product_id == Product.product_id)
        .join(base_agg, Product.product_id == base_agg.c.product_id)
        .outerjoin(SocialTS, and_(Product.product_id == SocialTS.product_id, SocialTS.dt >= start_date))
        .outerjoin(DeliveryTS, and_(Product.product_id == DeliveryTS.product_id, DeliveryTS.dt >= start_date))
        .where(UserFavorite.user_id == user_id)
        .group_by(Product.product_id, Product.subject)
    ).subquery("base_metrics")

    final_stmt = select(
        base_metrics,
        (base_metrics.c.total_revenue /
         over(func.sum(base_metrics.c.total_revenue), partition_by=base_metrics.c.subject)).label("category_share"),
        (over(func.sum(base_metrics.c.total_revenue), order_by=base_metrics.c.total_revenue.desc()) /
         func.nullif(over(func.sum(base_metrics.c.total_revenue)), 0)).label("cum_share_pct")
    )

    result = await session.execute(final_stmt)
    return result.all()