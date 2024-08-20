import pytest
from fastapi import status
from httpx import AsyncClient

# make all test mark with `asyncio`
pytestmark = pytest.mark.asyncio


async def test_root(async_client: AsyncClient):
    response = await async_client.get("/healthchecker")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "The API is LIVE!!"}


async def test_read_item(async_client: AsyncClient):
    response = await async_client.get("/items/1", params={"q": "test"})
    assert response.json() == {"item_id": 1, "q": "test"}
