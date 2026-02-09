import pytest
from sqlalchemy import text
from src.db.repositories.AnalyticsRepository import fetch_universal_data
from src.db.schemas.Analytics import AnalyticsRequest


@pytest.mark.asyncio
async def test_fetch_universal_data_abc_logic(db_session):
    await db_session.execute(text("""
        INSERT INTO users (id, user_id, email, password_hash, role, is_pro, is_active)
        VALUES (1, 12345, 'test@example.com', 'fake_hash', 'user', FALSE, TRUE)
    """))
    await db_session.execute(text("""
        INSERT INTO products (id, product_id, name, brand, subject, entity) VALUES
        (1, 10, 'Rich Item', 'BrandA', 'Coffee', 'item_entity'),
        (2, 20, 'Poor Item', 'BrandA', 'Coffee', 'item_entity')
    """))
    await db_session.execute(text("""
        INSERT INTO user_favorites (id, user_id, product_id)
        VALUES (1, 12345, 10), (2, 12345, 20)
    """))
    await db_session.execute(text("""
        INSERT INTO sales_proxy_ts (id, product_id, dt, sales, confidence) VALUES
        (1, 10, '2026-01-01', 9, 1.0), (2, 20, '2026-01-01', 1, 1.0)
    """))
    await db_session.execute(text("""
        INSERT INTO price_ts (id, product_id, dt, price_sale, discount_pct) VALUES
        (1, 10, '2026-01-01', 1000, 0.0), (2, 20, '2026-01-01', 1000, 0.0)
    """))
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
    await db_session.execute(text(f"""
        INSERT INTO users (id, user_id, email, password_hash, role, is_pro, is_active)
        VALUES (2, {uid}, 'no-sales@test.com', 'hash', 'user', FALSE, TRUE)
    """))
    await db_session.execute(text("""
        INSERT INTO products (id, product_id, name, brand, subject, entity) 
        VALUES (3, 30, 'Ghost Item', 'BrandB', 'Tea', 'item_entity')
    """))
    await db_session.execute(text(f"INSERT INTO user_favorites (id, user_id, product_id) VALUES (3, {uid}, 30)"))

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
    await db_session.execute(text(f"""
        INSERT INTO users (id, user_id, email, password_hash, role, is_pro, is_active)
        VALUES (4, {uid}, 'zero@test.com', 'hash', 'user', FALSE, TRUE)
    """))
    await db_session.execute(text("""
        INSERT INTO products (id, product_id, name, brand, subject, entity) 
        VALUES (4, 40, 'Free Item', 'BrandC', 'Gift', 'item_entity')
    """))
    await db_session.execute(text(f"INSERT INTO user_favorites (id, user_id, product_id) VALUES (4, {uid}, 40)"))

    await db_session.execute(text(
        "INSERT INTO sales_proxy_ts (id, product_id, dt, sales, confidence) VALUES (4, 40, '2026-01-01', 10, 1.0)"))
    await db_session.execute(text(
        "INSERT INTO price_ts (id, product_id, dt, price_sale, discount_pct) VALUES (4, 40, '2026-01-01', 0, 0.0)"))

    await db_session.flush()

    query = AnalyticsRequest(dimensions=["product_id"], metrics=["abc"], date_from="2026-01-01", date_to="2026-01-02")
    rows = await fetch_universal_data(db_session, user_id=uid, q=query)

    assert len(rows) == 1
    assert rows[0]['total_revenue'] == 0
    assert rows[0]['abc_sql'] == 'C'


@pytest.mark.asyncio
async def test_analytics_edge_date_overlap(db_session):
    uid = 777
    await db_session.execute(text(f"""
        INSERT INTO users (id, user_id, email, password_hash, role, is_pro, is_active)
        VALUES (5, {uid}, 'date@test.com', 'hash', 'user', FALSE, TRUE)
    """))

    await db_session.execute(text("""
        INSERT INTO products (id, product_id, name, brand, subject, entity) 
        VALUES (5, 50, 'Daily Item', 'BrandD', 'Tea', 'item_entity')
    """))

    await db_session.execute(text(f"INSERT INTO user_favorites (id, user_id, product_id) VALUES (5, {uid}, 50)"))

    await db_session.execute(text("""
        INSERT INTO sales_proxy_ts (id, product_id, dt, sales, confidence) VALUES 
        (5, 50, '2025-12-31', 5, 1.0), 
        (6, 50, '2026-01-01', 5, 1.0)
    """))

    await db_session.execute(text("""
        INSERT INTO price_ts (id, product_id, dt, price_sale, discount_pct) VALUES 
        (5, 50, '2025-12-31', 100, 0.0), 
        (6, 50, '2026-01-01', 100, 0.0)
    """))

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