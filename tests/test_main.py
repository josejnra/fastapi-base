import pytest
from _pytest.monkeypatch import MonkeyPatch
from fastapi import status
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis

from app.main import create_app

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


async def test_lifespan(monkeypatch: MonkeyPatch):
    """
    Tests the FastAPI application lifespan event by mocking the run_migrations function.

    Args:
        monkeypatch (MonkeyPatch): Pytest monkeypatch fixture for patching functions.

    Asserts:
        - The /docs endpoint returns HTTP 200 OK.
    """

    async def mock_run_migrations():
        print("Mocked run_migrations called")

    monkeypatch.setattr("app.main.run_migrations", mock_run_migrations)

    app = create_app()

    transport = ASGITransport(app=app)
    # AsyncClient to simulate a lifespan being applied
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/docs")

    assert response.status_code == status.HTTP_200_OK


async def test_slowapi(async_client: AsyncClient):
    """
    Tests the IP-based rate limiting using slowapi.

    Args:
        async_client (AsyncClient): The HTTPX async client.

    Asserts:
        - The root endpoint returns HTTP 200 OK for the first 5 requests.
        - The 6th request returns HTTP 429 TOO MANY REQUESTS.
    """
    for _ in range(5):
        response = await async_client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "The API is LIVE!!"}

    response = await async_client.get("/")
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


async def test_redis_rate_limiter(async_client: AsyncClient, redis_client: Redis):
    """
    Tests the Redis-based user rate limiter middleware.

    Args:
        async_client (AsyncClient): The HTTPX async client.
        redis_client (Redis): The Redis client.

    Asserts:
        - The /health endpoint returns HTTP 200 OK for the first 5 requests with the same user.
        - The 6th request returns HTTP 429 TOO MANY REQUESTS.
    """
    # delete all keys
    await redis_client.flushall()

    headers = {"x-user": "test health user"}
    for _ in range(5):
        response = await async_client.get("/health", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "The API is LIVE!!"}

    response = await async_client.get("/health", headers=headers)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
