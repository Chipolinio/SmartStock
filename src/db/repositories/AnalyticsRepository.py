from sqlalchemy import select, func, and_, case, cast, Float
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from typing import List

from src.db.models.Product import Product
from src.db.models.SalesProxyTS import SalesProxyTS
from src.db.models.PriceTS import PriceTS
from src.db.models.SocialTS import SocialTS
from src.db.models.DeliveryTS import DeliveryTS
from src.db.models.UserFavorite import UserFavorite
from src.db.models.StockTS import StockTS
from src.db.schemas.DashboardMetric import (
    SalesHistoryEntry, SalesHistoryResponse,
    StockDynamicsEntry, StockDynamicsResponse,
    ABCAnalysisEntry, ABCAnalysisResponse,
    XYZAnalysisEntry, XYZAnalysisResponse,
    TopProductEntry, TopProductsByRevenueResponse,
    TopProductsBySalesResponse,
    ProductsRatingEntry, ProductsRatingResponse,
    DashboardKPIResponse
)


async def get_sales_history(
    product_id: int,
    session: AsyncSession,
    days: int = 30
) -> SalesHistoryResponse:
    """
    Временной ряд продаж и выручки по дням.
    """
    start_date = date.today() - timedelta(days=days)
    
    stmt = (
        select(
            SalesProxyTS.dt,
            SalesProxyTS.sales,
            (SalesProxyTS.sales * PriceTS.price_sale).label("revenue")
        )
        .join(
            PriceTS,
            and_(
                PriceTS.product_id == SalesProxyTS.product_id,
                PriceTS.dt == SalesProxyTS.dt
            )
        )
        .where(
            SalesProxyTS.product_id == product_id,
            SalesProxyTS.dt >= start_date
        )
        .order_by(SalesProxyTS.dt.asc())
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    data = [
        SalesHistoryEntry(
            dt=row.dt,
            sales=row.sales,
            revenue=float(row.revenue) if row.revenue else 0.0
        )
        for row in rows
    ]
    
    return SalesHistoryResponse(product_id=product_id, data=data)


async def get_stock_dynamics(
    product_id: int,
    session: AsyncSession,
    days: int = 30
) -> StockDynamicsResponse:
    """
    Временной ряд остатков на складе по дням.
    """
    start_date = date.today() - timedelta(days=days)
    
    stmt = (
        select(StockTS.dt, StockTS.quantity)
        .where(
            StockTS.product_id == product_id,
            StockTS.dt >= start_date
        )
        .order_by(StockTS.dt.asc())
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    data = [
        StockDynamicsEntry(dt=row.dt, quantity=row.quantity)
        for row in rows
    ]
    
    return StockDynamicsResponse(product_id=product_id, data=data)


async def get_abc_data(
    user_id: int,
    session: AsyncSession,
    days: int = 30
) -> ABCAnalysisResponse:
    """
    ABC-анализ: классификация товаров по доле выручки.
    A — 80%, B — 15%, C — 5%
    """
    start_date = date.today() - timedelta(days=days)
    
    # Подзапрос: выручка по каждому товару
    revenue_subq = (
        select(
            Product.product_id,
            Product.name,
            Product.brand,
            Product.subject,
            func.sum(SalesProxyTS.sales * PriceTS.price_sale).label("total_revenue")
        )
        .join(SalesProxyTS, SalesProxyTS.product_id == Product.product_id)
        .join(PriceTS, and_(
            PriceTS.product_id == Product.product_id,
            PriceTS.dt == SalesProxyTS.dt
        ))
        .join(UserFavorite, UserFavorite.product_id == Product.product_id)
        .where(
            UserFavorite.user_id == user_id,
            SalesProxyTS.dt >= start_date
        )
        .group_by(Product.product_id, Product.name, Product.brand, Product.subject)
        .subquery("revenue_by_product")
    )
    
    # Общая выручка для расчёта доли
    total_revenue_subq = (
        select(func.sum(revenue_subq.c.total_revenue)).scalar_subquery()
    )
    
    # Расчёт доли и ABC-класса
    stmt = (
        select(
            revenue_subq.c.product_id,
            revenue_subq.c.name,
            revenue_subq.c.brand,
            revenue_subq.c.subject,
            revenue_subq.c.total_revenue,
            (revenue_subq.c.total_revenue / func.nullif(total_revenue_subq, 0)).label("revenue_share"),
        )
        .order_by(revenue_subq.c.total_revenue.desc())
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    # Расчёт кумулятивной суммы для ABC
    total_rev = sum(float(row.total_revenue) for row in rows)
    cumulative = 0.0
    data = []
    
    for row in rows:
        cumulative += float(row.total_revenue)
        cumulative_share = cumulative / total_rev if total_rev > 0 else 0
        
        if cumulative_share <= 0.8:
            abc_class = "A"
        elif cumulative_share <= 0.95:
            abc_class = "B"
        else:
            abc_class = "C"
        
        data.append(
            ABCAnalysisEntry(
                product_id=row.product_id,
                product_name=row.name,
                brand=row.brand,
                subject=row.subject,
                total_revenue=float(row.total_revenue),
                revenue_share=float(row.revenue_share) if row.revenue_share else 0.0,
                abc_class=abc_class
            )
        )
    
    return ABCAnalysisResponse(data=data)


async def get_xyz_data(
    user_id: int,
    session: AsyncSession,
    days: int = 30
) -> XYZAnalysisResponse:
    """
    XYZ-анализ: классификация по стабильности спроса.
    X — CV <= 0.1, Y — 0.1 < CV <= 0.25, Z — CV > 0.25
    """
    start_date = date.today() - timedelta(days=days)
    
    stmt = (
        select(
            Product.product_id,
            Product.name,
            Product.brand,
            Product.subject,
            func.avg(SalesProxyTS.sales).label("avg_sales"),
            func.stddev(SalesProxyTS.sales).label("sales_std")
        )
        .join(SalesProxyTS, SalesProxyTS.product_id == Product.product_id)
        .join(UserFavorite, UserFavorite.product_id == Product.product_id)
        .where(
            UserFavorite.user_id == user_id,
            SalesProxyTS.dt >= start_date
        )
        .group_by(Product.product_id, Product.name, Product.brand, Product.subject)
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    data = []
    for row in rows:
        avg_sales = float(row.avg_sales) if row.avg_sales else 0.0
        sales_std = float(row.sales_std) if row.sales_std else 0.0
        cv = sales_std / avg_sales if avg_sales > 0 else 0.0
        
        if cv <= 0.1:
            xyz_class = "X"
        elif cv <= 0.25:
            xyz_class = "Y"
        else:
            xyz_class = "Z"
        
        data.append(
            XYZAnalysisEntry(
                product_id=row.product_id,
                product_name=row.name,
                brand=row.brand,
                subject=row.subject,
                avg_sales=avg_sales,
                sales_std=sales_std,
                cv=cv,
                xyz_class=xyz_class
            )
        )
    
    return XYZAnalysisResponse(data=data)


async def get_top_products_by_revenue(
    user_id: int,
    session: AsyncSession,
    limit: int = 10,
    days: int = 30
) -> TopProductsByRevenueResponse:
    """Топ товаров по выручке."""
    start_date = date.today() - timedelta(days=days)
    
    stmt = (
        select(
            Product.product_id,
            Product.name,
            Product.brand,
            Product.subject,
            func.sum(SalesProxyTS.sales * PriceTS.price_sale).label("total_revenue"),
            func.sum(SalesProxyTS.sales).label("total_sales")
        )
        .join(SalesProxyTS, SalesProxyTS.product_id == Product.product_id)
        .join(PriceTS, and_(
            PriceTS.product_id == Product.product_id,
            PriceTS.dt == SalesProxyTS.dt
        ))
        .join(UserFavorite, UserFavorite.product_id == Product.product_id)
        .where(
            UserFavorite.user_id == user_id,
            SalesProxyTS.dt >= start_date
        )
        .group_by(Product.product_id, Product.name, Product.brand, Product.subject)
        .order_by(func.sum(SalesProxyTS.sales * PriceTS.price_sale).desc())
        .limit(limit)
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    data = [
        TopProductEntry(
            product_id=row.product_id,
            product_name=row.name,
            brand=row.brand,
            subject=row.subject,
            total_revenue=float(row.total_revenue),
            total_sales=int(row.total_sales),
            rank=idx + 1
        )
        for idx, row in enumerate(rows)
    ]
    
    return TopProductsByRevenueResponse(data=data)


async def get_top_products_by_sales(
    user_id: int,
    session: AsyncSession,
    limit: int = 10,
    days: int = 30
) -> TopProductsBySalesResponse:
    """Топ товаров по количеству продаж."""
    start_date = date.today() - timedelta(days=days)
    
    stmt = (
        select(
            Product.product_id,
            Product.name,
            Product.brand,
            Product.subject,
            func.sum(SalesProxyTS.sales).label("total_sales"),
            func.sum(SalesProxyTS.sales * PriceTS.price_sale).label("total_revenue")
        )
        .join(SalesProxyTS, SalesProxyTS.product_id == Product.product_id)
        .join(PriceTS, and_(
            PriceTS.product_id == Product.product_id,
            PriceTS.dt == SalesProxyTS.dt
        ))
        .join(UserFavorite, UserFavorite.product_id == Product.product_id)
        .where(
            UserFavorite.user_id == user_id,
            SalesProxyTS.dt >= start_date
        )
        .group_by(Product.product_id, Product.name, Product.brand, Product.subject)
        .order_by(func.sum(SalesProxyTS.sales).desc())
        .limit(limit)
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    data = [
        TopProductEntry(
            product_id=row.product_id,
            product_name=row.name,
            brand=row.brand,
            subject=row.subject,
            total_revenue=float(row.total_revenue),
            total_sales=int(row.total_sales),
            rank=idx + 1
        )
        for idx, row in enumerate(rows)
    ]
    
    return TopProductsBySalesResponse(data=data)


async def get_products_rating(
    user_id: int,
    session: AsyncSession,
    limit: int = 10,
    days: int = 30
) -> ProductsRatingResponse:
    """Рейтинг товаров по средней оценке."""
    start_date = date.today() - timedelta(days=days)
    
    stmt = (
        select(
            Product.product_id,
            Product.name,
            Product.brand,
            Product.subject,
            func.avg(SocialTS.rating).label("avg_rating"),
            func.max(SocialTS.feedbacks).label("feedbacks_count")
        )
        .join(SocialTS, SocialTS.product_id == Product.product_id)
        .join(UserFavorite, UserFavorite.product_id == Product.product_id)
        .where(
            UserFavorite.user_id == user_id,
            SocialTS.dt >= start_date
        )
        .group_by(Product.product_id, Product.name, Product.brand, Product.subject)
        .order_by(func.avg(SocialTS.rating).desc())
        .limit(limit)
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    data = [
        ProductsRatingEntry(
            product_id=row.product_id,
            product_name=row.name,
            brand=row.brand,
            subject=row.subject,
            avg_rating=float(row.avg_rating) if row.avg_rating else 0.0,
            feedbacks_count=row.feedbacks_count or 0,
            rank=idx + 1
        )
        for idx, row in enumerate(rows)
    ]
    
    return ProductsRatingResponse(data=data)


async def get_dashboard_kpi(
    user_id: int,
    session: AsyncSession,
    days: int = 30
) -> DashboardKPIResponse:
    """Общие метрики дашборда: выручка, продажи, рейтинг, количество товаров."""
    start_date = date.today() - timedelta(days=days)
    
    # Выручка и продажи
    revenue_stmt = (
        select(
            func.sum(SalesProxyTS.sales * PriceTS.price_sale).label("total_revenue"),
            func.sum(SalesProxyTS.sales).label("total_sales")
        )
        .join(PriceTS, and_(
            PriceTS.product_id == SalesProxyTS.product_id,
            PriceTS.dt == SalesProxyTS.dt
        ))
        .join(UserFavorite, UserFavorite.product_id == SalesProxyTS.product_id)
        .where(
            UserFavorite.user_id == user_id,
            SalesProxyTS.dt >= start_date
        )
    )
    
    # Рейтинг
    rating_stmt = (
        select(func.avg(SocialTS.rating).label("avg_rating"))
        .join(UserFavorite, UserFavorite.product_id == SocialTS.product_id)
        .where(
            UserFavorite.user_id == user_id,
            SocialTS.dt >= start_date
        )
    )
    
    # Количество товаров
    products_stmt = (
        select(func.count(func.distinct(UserFavorite.product_id)))
        .where(UserFavorite.user_id == user_id)
    )
    
    # Средняя доставка
    delivery_stmt = (
        select(func.avg(DeliveryTS.delivery_days))
        .join(UserFavorite, UserFavorite.product_id == DeliveryTS.product_id)
        .where(
            UserFavorite.user_id == user_id,
            DeliveryTS.dt >= start_date
        )
    )

    revenue_result = await session.execute(revenue_stmt)
    revenue_row = revenue_result.first()

    rating_result = await session.execute(rating_stmt)
    rating_row = rating_result.first()

    products_result = await session.execute(products_stmt)
    products_count = products_result.scalar()

    delivery_result = await session.execute(delivery_stmt)
    delivery_avg = delivery_result.scalar()

    # Товары с риском OOS (остаток < 7 дней продаж)
    # Упрощённый запрос: считаем товары, где средний остаток < 7 * средние продажи
    oos_count = 0
    try:
        oos_subq = (
            select(
                Product.product_id,
                func.avg(StockTS.quantity).label("avg_stock"),
                func.avg(SalesProxyTS.sales).label("avg_sales")
            )
            .join(StockTS, StockTS.product_id == Product.product_id)
            .outerjoin(SalesProxyTS, SalesProxyTS.product_id == Product.product_id)
            .join(UserFavorite, UserFavorite.product_id == Product.product_id)
            .where(UserFavorite.user_id == user_id)
            .group_by(Product.product_id)
            .having(func.avg(StockTS.quantity) < 7 * func.coalesce(func.avg(SalesProxyTS.sales), 1))
        )
        oos_result = await session.execute(oos_subq)
        oos_count = len(oos_result.all())
    except Exception:
        pass  # Игнорируем ошибки подсчёта OOS
    
    return DashboardKPIResponse(
        total_revenue=float(revenue_row.total_revenue) if revenue_row and revenue_row.total_revenue else 0.0,
        total_sales=int(revenue_row.total_sales) if revenue_row and revenue_row.total_sales else 0,
        avg_rating=float(rating_row.avg_rating) if rating_row and rating_row.avg_rating else 0.0,
        total_products=products_count or 0,
        avg_delivery_days=float(delivery_avg) if delivery_avg else None,
        oos_risk_count=0  # Заглушка, требует доработки подзапроса
    )
