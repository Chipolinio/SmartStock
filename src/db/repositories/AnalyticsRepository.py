from sqlalchemy import select, func, and_, over, case
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from src.db.models import Product, SalesProxyTS, PriceTS, SocialTS, DeliveryTS, UserFavorite
from src.db.schemas.Analytics import AnalyticsRequest


async def fetch_universal_data(
        session: AsyncSession,
        user_id: int,
        q: AnalyticsRequest
) -> List[Dict[str, Any]]:
    sales_subq = (
        select(
            SalesProxyTS.product_id,
            func.sum(func.coalesce(SalesProxyTS.sales, 0)).label("total_sales"),
            func.avg(SalesProxyTS.sales).label("sales_avg"),
            func.stddev(SalesProxyTS.sales).label("sales_std"),
            func.sum(func.coalesce(SalesProxyTS.sales, 0) * PriceTS.price_sale).label("total_revenue")
        )
        .join(PriceTS, and_(
            PriceTS.product_id == SalesProxyTS.product_id,
            PriceTS.dt == SalesProxyTS.dt
        ))
        .where(SalesProxyTS.dt.between(q.date_from, q.date_to))
        .group_by(SalesProxyTS.product_id)
    ).subquery("sales_agg")

    social_subq = (
        select(
            SocialTS.product_id,
            func.avg(SocialTS.rating).label("avg_rating"),
            func.max(SocialTS.feedbacks).label("max_feedbacks")
        )
        .where(SocialTS.dt.between(q.date_from, q.date_to))
        .group_by(SocialTS.product_id)
    ).subquery("social_agg")

    delivery_subq = (
        select(
            DeliveryTS.product_id,
            func.avg(DeliveryTS.delivery_days).label("avg_delivery")
        )
        .where(DeliveryTS.dt.between(q.date_from, q.date_to))
        .group_by(DeliveryTS.product_id)
    ).subquery("delivery_agg")

    dim_map = {
        "dt": SalesProxyTS.dt,
        "brand": Product.brand,
        "subject": Product.subject,
        "product_id": Product.product_id
    }
    dims = [dim_map[d] for d in q.dimensions]

    base_stmt = (
        select(
            *dims,
            func.sum(sales_subq.c.total_sales).label("total_sales"),
            func.sum(sales_subq.c.total_revenue).label("total_revenue"),
            func.avg(sales_subq.c.sales_std).label("sales_std"),
            func.avg(sales_subq.c.sales_avg).label("sales_avg"),
            func.avg(social_subq.c.avg_rating).label("avg_rating"),
            func.max(social_subq.c.max_feedbacks).label("max_feedbacks"),
            func.avg(delivery_subq.c.avg_delivery).label("avg_delivery")
        )
        .join(Product, Product.product_id == sales_subq.c.product_id)
        .join(UserFavorite, and_(
            UserFavorite.product_id == Product.product_id,
            UserFavorite.user_id == user_id
        ))
        .outerjoin(social_subq, social_subq.c.product_id == Product.product_id)
        .outerjoin(delivery_subq, delivery_subq.c.product_id == Product.product_id)
    )

    if "dt" in q.dimensions:
        base_stmt = base_stmt.join(SalesProxyTS, and_(
            SalesProxyTS.product_id == Product.product_id,
            SalesProxyTS.dt.between(q.date_from, q.date_to)
        ))

    if q.filters:
        for key, vals in q.filters.items():
            if hasattr(Product, key) and vals:
                base_stmt = base_stmt.where(getattr(Product, key).in_(vals))

    base_stmt = base_stmt.group_by(*dims)

    main_subq = base_stmt.subquery()

    if "product_id" in q.dimensions and "subject" in q.dimensions:
        partition_by = main_subq.c.subject
    else:
        partition_by = None

    final_stmt = select(
        main_subq,
        case(
            (over(func.sum(main_subq.c.total_revenue),
                  partition_by=partition_by,
                  order_by=main_subq.c.total_revenue.desc()) /
             func.nullif(over(func.sum(main_subq.c.total_revenue), partition_by=partition_by), 0) <= 0.8, 'A'),
            (over(func.sum(main_subq.c.total_revenue),
                  partition_by=partition_by,
                  order_by=main_subq.c.total_revenue.desc()) /
             func.nullif(over(func.sum(main_subq.c.total_revenue), partition_by=partition_by), 0) <= 0.95, 'B'),
            else_='C'
        ).label("abc_sql")
    )

    result = await session.execute(final_stmt)
    return [dict(row) for row in result.mappings()]