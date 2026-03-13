import pytest
from httpx import AsyncClient, ASGITransport
from main import app


# pytest-asyncio lets pytest run async test functions
@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_get_transactions_returns_200():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/transactions")
    assert response.status_code == 200
    assert "data" in response.json()


@pytest.mark.asyncio
async def test_get_transactions_with_filters():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/transactions?country=India&year=2022")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_summary():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/transactions/summary")
    assert response.status_code == 200
    assert "data" in response.json()


@pytest.mark.asyncio
async def test_get_countries():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/geography/countries")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_organizations():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/organizations")
    assert response.status_code == 200