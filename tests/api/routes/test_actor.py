from typing import Any

import pytest
from faker import Faker
from fastapi import status
from httpx import AsyncClient

from app.core.config import get_settings

# make all test mark with `asyncio`
pytestmark = pytest.mark.asyncio


@pytest.fixture
def fake_actor() -> dict[str, Any]:
    fake = Faker()

    return {"name": fake.name(), "age": fake.random_int(min=18, max=100)}


@pytest.fixture
def fake_actors(request: pytest.FixtureRequest) -> list[dict[str, Any]]:
    n = request.param
    fake = Faker()
    actors = [
        {"name": fake.name(), "age": fake.random_int(min=18, max=100)} for _ in range(n)
    ]
    return actors


async def test_create_actor_success(
    async_client: AsyncClient, fake_actor: dict[str, Any]
):
    """Actor is created successfully."""
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/actors/", json=fake_actor
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()
    assert response_json["name"] == fake_actor["name"]
    assert response_json["age"] == fake_actor["age"]


async def test_create_actor_missing_field(async_client: AsyncClient):
    """Fail to create an actor with missing field."""
    fake = Faker()
    actor = {"name": fake.name()}
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/actors/", json=actor
    )
    # TODO: improve error message
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_create_actor_too_many_fields(
    async_client: AsyncClient, fake_actor: dict[str, Any]
):
    """Fail to create an actor with too many field."""
    fake_actor["new_field_1"] = "new_field_1"
    fake_actor["new_field_2"] = "new_field_2"
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/actors/", json=fake_actor
    )
    assert response.status_code == status.HTTP_201_CREATED


async def test_get_actor(async_client: AsyncClient, fake_actor: dict[str, Any]):
    """Successfully retrieve an actor."""
    # TODO: populate database with actors instead of creating them one by one
    actor_created = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/actors/", json=fake_actor
    )
    actor_id = actor_created.json()["id"]
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/actors/{actor_id}"
    )
    assert response.status_code == status.HTTP_200_OK


async def test_get_actor_not_found(async_client: AsyncClient):
    """When an actor is not found."""
    response = await async_client.get(f"{get_settings().API_ROOT_PATH}/actors/{99999}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("fake_actors", [0, 1, 5], indirect=True)
async def test_get_actors(async_client: AsyncClient, fake_actors: list[dict[str, Any]]):
    """Get list of actors for 0, 1 and many actors."""
    # TODO: populate database with actors instead of creating them one by one
    # create actors
    for actor in fake_actors:
        await async_client.post(f"{get_settings().API_ROOT_PATH}/actors/", json=actor)

    # get actors
    response = await async_client.get(f"{get_settings().API_ROOT_PATH}/actors/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == len(fake_actors)


@pytest.mark.parametrize("fake_actors", [11], indirect=True)
async def test_get_actors_with_pagination(
    async_client: AsyncClient, fake_actors: list[dict[str, Any]]
):
    """Get list of actors for 0, 1 and many actors."""
    # TODO: populate database with actors instead of creating them one by one
    # create actors
    for actor in fake_actors:
        await async_client.post(f"{get_settings().API_ROOT_PATH}/actors/", json=actor)

    # get actors
    page_size = 10
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/actors/", params={"page_size": page_size}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == len(fake_actors)

    # get actors
    page_size = 10
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/actors/", params={"page_size": page_size}
    )
    response = await async_client.get(f"{get_settings().API_ROOT_PATH}/actors/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == len(fake_actors)
    assert len(response.json()["actors"]) == page_size
