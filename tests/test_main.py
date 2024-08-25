import pytest
from _pytest.monkeypatch import MonkeyPatch
from fastapi import status
from httpx import AsyncClient
from redis.asyncio import Redis

from app.main import create_app

# make all test mark with `asyncio`
pytestmark = pytest.mark.asyncio


async def test_lifespan(monkeypatch: MonkeyPatch):
    # Mocker run_migrations in order to make sure it's being called, but do nothing
    async def mock_run_migrations():
        print("Mocked run_migrations called")

    monkeypatch.setattr("app.main.run_migrations", mock_run_migrations)

    app = create_app()

    # AsyncClient to simulate a lifespan being applied
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/docs")

    assert response.status_code == status.HTTP_200_OK


async def test_slowapi(async_client: AsyncClient):
    for _ in range(5):
        response = await async_client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "The API is LIVE!!"}

    response = await async_client.get("/")
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


async def test_redis_rate_limiter(async_client: AsyncClient, redis_client: Redis):
    # delete all keys
    await redis_client.flushall()

    headers = {"x-user": "test health user"}
    for _ in range(5):
        response = await async_client.get("/health", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "The API is LIVE!!"}

    response = await async_client.get("/health", headers=headers)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
