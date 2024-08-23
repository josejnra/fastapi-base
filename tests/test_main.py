import pytest
from _pytest.monkeypatch import MonkeyPatch
from fastapi import status
from httpx import AsyncClient

from app.main import create_app

# make all test mark with `asyncio`
pytestmark = pytest.mark.asyncio


async def test_root(async_client: AsyncClient):
    response = await async_client.get("/healthchecker")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "The API is LIVE!!"}


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
