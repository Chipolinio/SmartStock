import pytest
from httpx import AsyncClient
from unittest.mock import patch
from fastapi import status


@pytest.fixture
def mock_user_auth():
    with patch("src.utils.dependencies.decode_token") as mocked:
        mocked.return_value = {
            "sub": "12345",
            "role": "user",
            "is_pro": True,
            "is_active": True
        }
        yield mocked


@pytest.mark.asyncio
async def test_aggregate_validation_error_empty_metrics(client: AsyncClient, mock_user_auth):
    client.cookies.set("access_token", "any-token")
    payload = {
        "date_from": "2026-01-01",
        "date_to": "2026-01-02",
        "dimensions": ["product_id"],
        "metrics": [],
        "filters": {}
    }
    response = await client.post("/analytics/aggregate", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_aggregate_validation_error_invalid_dimension(client: AsyncClient, mock_user_auth):
    client.cookies.set("access_token", "any-token")
    payload = {
        "date_from": "2026-01-01",
        "date_to": "2026-01-02",
        "dimensions": ["invalid_field"],
        "metrics": ["revenue"],
        "filters": {}
    }
    response = await client.post("/analytics/aggregate", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_aggregate_unauthorized(client: AsyncClient):
    client.cookies.clear()
    payload = {
        "date_from": "2026-01-01",
        "date_to": "2026-01-02",
        "dimensions": ["product_id"],
        "metrics": ["revenue"]
    }
    response = await client.post("/analytics/aggregate", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
@patch("src.services.AnalyticsService.run_unified_analytics")
async def test_aggregate_server_error_handling(mock_service, client: AsyncClient, mock_user_auth):
    mock_service.side_effect = Exception("Database is down")
    client.cookies.set("access_token", "valid-token")

    payload = {
        "date_from": "2026-01-01",
        "date_to": "2026-01-02",
        "dimensions": ["product_id"],
        "metrics": ["revenue"]
    }

    with pytest.raises(Exception) as excinfo:
        await client.post("/analytics/aggregate", json=payload)

    assert "Database is down" in str(excinfo.value)
@pytest.mark.asyncio
async def test_pro_access_logic(client: AsyncClient, mock_user_auth):
    mock_user_auth.return_value["is_pro"] = False
    client.cookies.set("access_token", "token-for-non-pro")

    payload = {
        "date_from": "2026-01-01",
        "date_to": "2026-01-02",
        "dimensions": ["product_id"],
        "metrics": ["abc"]
    }

    response = await client.post("/analytics/aggregate", json=payload)

    assert response.status_code == status.HTTP_200_OK