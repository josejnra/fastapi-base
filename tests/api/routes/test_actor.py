from typing import Any

import pytest
from faker import Faker
from fastapi import status
from httpx import AsyncClient

from app.core.config import get_settings
from app.models import Actor, Address
from app.schemas import ActorResponseDetailed

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture
def fake_actor() -> dict[str, Any]:
    """
    Provides a fake actor dictionary for testing.

    Returns:
        dict[str, Any]: A dictionary with random name and age.
    """
    fake = Faker()
    return {"name": fake.name(), "age": fake.random_int(min=18, max=100)}


async def test_create_actor_success(
    async_client: AsyncClient, fake_actor: dict[str, Any]
):
    """
    Test that an actor is created successfully.

    Args:
        async_client (AsyncClient): The HTTPX async client.
        fake_actor (dict[str, Any]): The fake actor data.

    Asserts:
        - Status code is 201 CREATED.
        - Response contains correct name and age.
        - Movies and addresses lists are empty.
    """
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/actors/", json=fake_actor
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()
    assert response_json["name"] == fake_actor["name"]
    assert response_json["age"] == fake_actor["age"]
    assert len(response_json["movies"]) == 0
    assert len(response_json["addresses"]) == 0


async def test_create_actor_missing_field(async_client: AsyncClient):
    """
    Test failure to create an actor with a missing field.

    Args:
        async_client (AsyncClient): The HTTPX async client.

    Asserts:
        - Status code is 422 UNPROCESSABLE ENTITY.
    """
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
    """
    Test creating an actor with extra fields (should ignore extras).

    Args:
        async_client (AsyncClient): The HTTPX async client.
        fake_actor (dict[str, Any]): The fake actor data.

    Asserts:
        - Status code is 201 CREATED.
    """
    fake_actor["new_field_1"] = "new_field_1"
    fake_actor["new_field_2"] = "new_field_2"
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/actors/", json=fake_actor
    )
    assert response.status_code == status.HTTP_201_CREATED


async def test_get_actor(
    async_client: AsyncClient,
    auth_header: dict[str, str],
    seed_addresses: list[Address],
):
    """
    Test successfully retrieving an actor by ID.

    Args:
        async_client (AsyncClient): The HTTPX async client.
        auth_header (dict[str, str]): Authorization header.
        seed_addresses (list[Address]): Seeded addresses.

    Asserts:
        - Status code is 200 OK.
        - Response contains correct actor ID and address count.
    """
    # actor with 1 address
    count_addresses = 1
    first_actor = seed_addresses[1].actor
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/actors/{first_actor.id}", headers=auth_header
    )
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_json["id"] == first_actor.id
    assert response_json["addresses"] is not None
    assert len(response_json["addresses"]) == count_addresses

    # actor with 2 addresses
    count_addresses = 2
    first_actor = seed_addresses[0].actor
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/actors/{first_actor.id}", headers=auth_header
    )
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_json["id"] == first_actor.id
    assert response_json["addresses"] is not None
    assert len(response_json["addresses"]) == count_addresses


async def test_get_actor_not_found(
    async_client: AsyncClient, auth_header: dict[str, str]
):
    """
    Test retrieving a non-existent actor returns 404.

    Args:
        async_client (AsyncClient): The HTTPX async client.
        auth_header (dict[str, str]): Authorization header.

    Asserts:
        - Status code is 404 NOT FOUND.
    """
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/actors/{99999}", headers=auth_header
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("seed_actors", [0, 1, 5], indirect=True)
async def test_get_actors(
    async_client: AsyncClient, auth_header: dict[str, str], seed_actors: list[Actor]
):
    """
    Test retrieving a list of actors for 0, 1, and many actors.

    Args:
        async_client (AsyncClient): The HTTPX async client.
        auth_header (dict[str, str]): Authorization header.
        seed_actors (list[Actor]): Seeded actors.

    Asserts:
        - Status code is 200 OK.
        - Response contains correct total and page size.
        - Movies list is empty for each actor.
    """
    movie_list_len = 0

    # no params
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/actors/", headers=auth_header
    )
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_json["total"] == len(seed_actors)
    if len(seed_actors) > 0:
        assert len(response_json["actors"][0]["movies"]) == movie_list_len
        assert ActorResponseDetailed(**response_json["actors"][0])

    # set page size
    page_size = 1
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/actors/",
        headers=auth_header,
        params={"page_size": page_size},
    )
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_json["total"] == len(seed_actors)
    assert response_json["page_size"] == page_size
    if len(seed_actors) > 0:
        assert len(response_json["actors"][0]["movies"]) == movie_list_len
        assert len(response_json["actors"]) == page_size
        assert ActorResponseDetailed(**response_json["actors"][0])


async def test_get_actors_wrong_page_values(
    async_client: AsyncClient, auth_header: dict[str, str], seed_actors: list[Actor]
):
    """
    Test validation for wrong page size parameter when getting actors.

    Args:
        async_client (AsyncClient): The HTTPX async client.
        auth_header (dict[str, str]): Authorization header.
        seed_actors (list[Actor]): Seeded actors.

    Asserts:
        - Status code is 422 UNPROCESSABLE ENTITY for invalid page size.
    """
    print(f"seed_actors: {len(seed_actors)}")
    # page size is 0
    page_size = 0
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/actors/",
        headers=auth_header,
        params={"page_size": page_size},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
