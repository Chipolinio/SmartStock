import pytest
from src.services.AnalyticsService import get_recommendation_text, run_unified_analytics
from src.db.schemas.Analytics import AnalyticsRequest


def test_recommendation_logic():
    assert "Хит" in get_recommendation_text("A", "X", 0.8)
    assert "Неликвид" in get_recommendation_text("C", "Z", 0.5)
    assert "Срочно" in get_recommendation_text("B", "Y", 0.3)


@pytest.mark.asyncio
async def test_xyz_and_score_calculation(mocker):
    mock_raw_data = [{
        "product_id": 1,
        "total_revenue": 1000,
        "total_sales": 10,
        "sales_avg": 2,
        "sales_std": 0.1,
        "avg_rating": 5,
        "max_feedbacks": 100,
        "avg_delivery": 1,
        "abc_sql": "A"
    }]
    mocker.patch("src.services.AnalyticsService.fetch_universal_data", return_value=mock_raw_data)

    query = AnalyticsRequest(
        dimensions=["product_id"],
        metrics=["revenue", "xyz", "score"],
        date_from="2026-01-01",
        date_to="2026-01-07"
    )

    results = await run_unified_analytics(None, user_id=1, q=query)

    assert results[0].metrics.xyz == "X"
    assert results[0].metrics.score == 0.69