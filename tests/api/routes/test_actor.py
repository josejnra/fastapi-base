import pytest
from faker import Faker
from fastapi import status
from httpx import AsyncClient

from app.core.config import get_settings

# make all test mark with `asyncio`
pytestmark = pytest.mark.asyncio


# --------------------------------
# Actor
# --------------------------------
async def test_create_actor(async_client: AsyncClient):
    """Test if the actor is created successfully."""
    fake = Faker()

    actor = {"name": fake.name(), "age": fake.random_int(min=18, max=100)}

    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/actors/", json=actor
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()
    assert response_json["name"] == actor["name"]
    assert response_json["age"] == actor["age"]
    print(response_json)

    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/actors/{response_json["id"]}"
    )
    assert response.status_code == status.HTTP_200_OK


async def test_actor_not_found(async_client: AsyncClient):
    """Test when an actor is not found."""
    response = await async_client.get(f"{get_settings().API_ROOT_PATH}/actors/{10}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_actors_empty_list(async_client: AsyncClient):
    response = await async_client.get(f"{get_settings().API_ROOT_PATH}/actors/")
    assert response.status_code == status.HTTP_200_OK
