from sqlalchemy import select, func, and_, over
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.db.models import Product, PriceTS, SalesProxyTS, SocialTS, DeliveryTS, UserFavorite

async def get_analytics_dataset(session: AsyncSession, user_id: int, days: int = 30):
    """
    Сбор данных через таблицу связей UserFavorite с использованием Window Functions.
    """
    start_date = date.today() - timedelta(days=days)

    # 1. Агрегируем метрики по товарам пользователя
    # Используем подзапрос, чтобы сначала собрать базу
    base_metrics = (
        select(
            Product.product_id,
            Product.subject,
            func.avg(PriceTS.price_sale).label("avg_price"),
            func.sum(SalesProxyTS.sales).label("total_sales"),
            func.stddev(SalesProxyTS.sales).label("sales_std"),
            func.avg(SalesProxyTS.sales).label("sales_avg"),
            func.avg(SocialTS.rating).label("avg_rating"),
            func.max(SocialTS.feedbacks).label("max_feedbacks"),
            func.avg(DeliveryTS.delivery_days).label("avg_delivery"),
            func.sum(SalesProxyTS.sales * PriceTS.price_sale).label("total_revenue")
        )
        .join(UserFavorite, UserFavorite.product_id == Product.product_id)
        .join(PriceTS, Product.product_id == PriceTS.product_id)
        .outerjoin(SalesProxyTS, and_(Product.product_id == SalesProxyTS.product_id, SalesProxyTS.dt == PriceTS.dt))
        .outerjoin(SocialTS, and_(Product.product_id == SocialTS.product_id, SocialTS.dt == PriceTS.dt))
        .outerjoin(DeliveryTS, and_(Product.product_id == DeliveryTS.product_id, DeliveryTS.dt == PriceTS.dt))
        .where(UserFavorite.user_id == user_id)
        .where(PriceTS.dt >= start_date)
        .group_by(Product.product_id, Product.subject)
    ).subquery()

    # 2. Оконные функции поверх агрегатов
    final_stmt = select(
        base_metrics,
        # Доля выручки товара внутри его категории (Window Function)
        (base_metrics.c.total_revenue /
         over(func.sum(base_metrics.c.total_revenue), partition_by=base_metrics.c.subject)).label("category_share"),
        # Кумулятивный процент выручки для автоматического ABC
        (over(func.sum(base_metrics.c.total_revenue), order_by=base_metrics.c.total_revenue.desc()) /
         over(func.sum(base_metrics.c.total_revenue))).label("cum_share_pct")
    )

    result = await session.execute(final_stmt)
    return result.all()