import pytest
from datetime import date
from src.db.models import User, Product, UserFavorite, SalesProxyTS, PriceTS
from src.db.repositories.AnalyticsRepository import fetch_universal_data
from src.db.schemas.Analytics import AnalyticsRequest


@pytest.mark.asyncio
async def test_fetch_universal_data_abc_logic(db_session):
    # Создаем пользователя
    db_session.add(User(id=1, user_id=12345, email='test@example.com', password_hash='fake_hash', role='user'))

    # Создаем продукты
    db_session.add_all([
        Product(id=1, product_id=10, name='Rich Item', brand='BrandA', subject='Coffee', entity='item_entity'),
        Product(id=2, product_id=20, name='Poor Item', brand='BrandA', subject='Coffee', entity='item_entity')
    ])

    # Избранное
    db_session.add_all([
        UserFavorite(id=1, user_id=12345, product_id=10),
        UserFavorite(id=2, user_id=12345, product_id=20)
    ])

    # Продажи и цены
    dt = date(2026, 1, 1)
    db_session.add_all([
        SalesProxyTS(id=1, product_id=10, dt=dt, sales=9, confidence=1.0),
        SalesProxyTS(id=2, product_id=20, dt=dt, sales=1, confidence=1.0),
        PriceTS(id=1, product_id=10, dt=dt, price_sale=1000.0, discount_pct=0.0),
        PriceTS(id=2, product_id=20, dt=dt, price_sale=1000.0, discount_pct=0.0)
    ])

    await db_session.flush()

    query = AnalyticsRequest(
        dimensions=["product_id"],
        metrics=["abc", "revenue"],
        date_from="2026-01-01",
        date_to="2026-01-02"
    )
    rows = await fetch_universal_data(db_session, user_id=12345, q=query)
    assert len(rows) >= 2


@pytest.mark.asyncio
async def test_analytics_edge_no_sales_item(db_session):
    uid = 54321
    db_session.add(User(id=2, user_id=uid, email='no-sales@test.com', password_hash='hash', role='user'))
    db_session.add(Product(id=3, product_id=30, name='Ghost Item', brand='BrandB', subject='Tea', entity='item_entity'))
    db_session.add(UserFavorite(id=3, user_id=uid, product_id=30))

    await db_session.flush()

    query = AnalyticsRequest(
        dimensions=["product_id"],
        metrics=["abc", "revenue"],
        date_from="2026-01-01",
        date_to="2026-01-02"
    )
    rows = await fetch_universal_data(db_session, user_id=uid, q=query)

    assert len(rows) == 1
    assert rows[0]['total_sales'] == 0
    assert rows[0]['abc_sql'] == 'C'


@pytest.mark.asyncio
async def test_analytics_edge_zero_price_division(db_session):
    uid = 999
    db_session.add(User(id=4, user_id=uid, email='zero@test.com', password_hash='hash', role='user'))
    db_session.add(Product(id=4, product_id=40, name='Free Item', brand='BrandC', subject='Gift', entity='item_entity'))
    db_session.add(UserFavorite(id=4, user_id=uid, product_id=40))

    dt = date(2026, 1, 1)
    db_session.add(SalesProxyTS(id=4, product_id=40, dt=dt, sales=10, confidence=1.0))
    db_session.add(PriceTS(id=4, product_id=40, dt=dt, price_sale=0.0, discount_pct=0.0))

    await db_session.flush()

    query = AnalyticsRequest(dimensions=["product_id"], metrics=["abc"], date_from="2026-01-01", date_to="2026-01-02")
    rows = await fetch_universal_data(db_session, user_id=uid, q=query)

    assert len(rows) == 1
    assert rows[0]['total_revenue'] == 0
    assert rows[0]['abc_sql'] == 'C'


@pytest.mark.asyncio
async def test_analytics_edge_date_overlap(db_session):
    uid = 777
    db_session.add(User(id=5, user_id=uid, email='date@test.com', password_hash='hash', role='user'))
    db_session.add(Product(id=5, product_id=50, name='Daily Item', brand='BrandD', subject='Tea', entity='item_entity'))
    db_session.add(UserFavorite(id=5, user_id=uid, product_id=50))

    d1, d2 = date(2025, 12, 31), date(2026, 1, 1)
    db_session.add_all([
        SalesProxyTS(id=5, product_id=50, dt=d1, sales=5, confidence=1.0),
        SalesProxyTS(id=6, product_id=50, dt=d2, sales=5, confidence=1.0),
        PriceTS(id=5, product_id=50, dt=d1, price_sale=100.0, discount_pct=0.0),
        PriceTS(id=6, product_id=50, dt=d2, price_sale=100.0, discount_pct=0.0)
    ])

    await db_session.flush()

    query = AnalyticsRequest(
        dimensions=["product_id"],
        metrics=["sales"],
        date_from="2025-12-31",
        date_to="2026-01-01"
    )
    rows = await fetch_universal_data(db_session, user_id=uid, q=query)

    assert len(rows) == 1
    assert rows[0]['total_sales'] == 10