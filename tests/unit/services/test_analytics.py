import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException
from src.services.AnalyticsService import run_unified_analytics, get_recommendation_text
from src.db.schemas.Analytics import AnalyticsRequest


def test_get_recommendation_text():
    assert "Хит" in get_recommendation_text("A", "X", 0.9)
    assert "Неликвид" in get_recommendation_text("C", "Z", 0.5)
    assert "Срочно" in get_recommendation_text("B", "Y", 0.3)  # Низкий скоринг


@pytest.mark.asyncio
async def test_run_unified_analytics_edge_cases(mocker):
    mock_raw_rows = [
        {
            "product_id": 999,
            "sales_std": 10.0,
            "sales_avg": 0.0,
            "avg_rating": 10.0,
            "max_feedbacks": 1000,
            "avg_delivery": 1,
            "abc_sql": "C"
        }
    ]

    mocker.patch(
        "src.states.AnalyticsService.fetch_universal_data",
        new_callable=AsyncMock,
        return_value=mock_raw_rows
    )

    query = AnalyticsRequest(
        dimensions=["product_id"],
        metrics=["xyz", "score"],
        date_from="2026-01-01",
        date_to="2026-01-02"
    )

    results = await run_unified_analytics(AsyncMock(), user_id=1, q=query)
    res = results[0]

    assert res.metrics.xyz == "X"
    assert res.metrics.score == 1.0


@pytest.mark.asyncio
async def test_run_unified_analytics_partial_metrics(mocker):
    mock_raw_rows = [{"product_id": 1, "total_revenue": 500.0}]

    mocker.patch(
        "src.states.AnalyticsService.fetch_universal_data",
        new_callable=AsyncMock,
        return_value=mock_raw_rows
    )

    # Просим ТОЛЬКО выручку
    query = AnalyticsRequest(
        dimensions=["product_id"],
        metrics=["revenue"],
        date_from="2026-01-01",
        date_to="2026-01-02"
    )

    results = await run_unified_analytics(AsyncMock(), user_id=1, q=query)
    metrics = results[0].metrics

    assert metrics.revenue == 500.0
    assert metrics.abc is None
    assert metrics.xyz is None
    assert metrics.score is None


@pytest.mark.asyncio
async def test_run_unified_analytics_success(mocker):
    mock_raw_rows = [
        {
            "product_id": 101,
            "total_revenue": 1000.0,
            "total_sales": 10,
            "sales_std": 0.5,
            "sales_avg": 5.0,
            "avg_rating": 4.5,
            "max_feedbacks": 100,
            "avg_delivery": 2,
            "abc_sql": "A"
        }
    ]

    mock_fetch = mocker.patch(
        "src.states.AnalyticsService.fetch_universal_data",
        new_callable=AsyncMock,
        return_value=mock_raw_rows
    )

    query = AnalyticsRequest(
        dimensions=["product_id"],
        metrics=["revenue", "abc", "xyz", "score", "recommendation"],
        date_from="2026-01-01",
        date_to="2026-01-02"
    )

    results = await run_unified_analytics(AsyncMock(), user_id=1, q=query)
    res = results[0]

    assert res.dimensions["product_id"] == 101
    assert res.metrics.revenue == 1000.0
    assert res.metrics.xyz == "X"
    assert res.metrics.score > 0
    assert isinstance(res.recommendation, str)


@pytest.mark.asyncio
async def test_run_unified_analytics_error(mocker):
    mocker.patch(
        "src.states.AnalyticsService.fetch_universal_data",
        side_effect=Exception("DB connection lost")
    )

    query = AnalyticsRequest(
        dimensions=["dt"],
        metrics=["revenue"],
        date_from="2026-01-01",
        date_to="2026-01-02"
    )

    with pytest.raises(HTTPException) as exc:
        await run_unified_analytics(AsyncMock(), user_id=1, q=query)

    assert exc.value.status_code == 500