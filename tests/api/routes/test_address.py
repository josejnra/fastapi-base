from typing import Any

import pytest
from faker import Faker
from fastapi import status
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.models import Actor

# make all test mark with `asyncio`
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def seed_actors(db_session: AsyncSession) -> bool:
    """Fixture to seed actors."""
    fake = Faker()
    actors = [
        Actor(id=i, name=fake.name(), age=fake.random_int(min=10, max=90))
        for i in range(1, 4)
    ]
    db_session.add_all(actors)
    await db_session.commit()
    return True


@pytest.fixture
def fake_address() -> dict[str, Any]:
    fake = Faker()

    return {
        "country": fake.country(),
        "city": fake.city(),
        "address_line_1": fake.address(),
        "address_line_2": fake.street_address(),
        "post_code": fake.postcode(),
        "actor_id": fake.random_int(min=1, max=3),
    }


@pytest.fixture
def fake_addresses(request: pytest.FixtureRequest) -> list[dict[str, Any]]:
    n = request.param
    fake = Faker()
    addresses = [
        {
            "country": fake.country(),
            "city": fake.city(),
            "address_line_1": fake.address(),
            "address_line_2": fake.street_address(),
            "post_code": fake.postcode(),
            "actor_id": fake.random_int(min=1, max=3),
        }
        for _ in range(n)
    ]
    return addresses


async def test_create_address_success(
    async_client: AsyncClient, fake_address: dict[str, Any], seed_actors: bool
):
    """address is created successfully."""
    print("SEED ACTORS", seed_actors)
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/addresses/", json=fake_address
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()

    assert response_json["country"] == fake_address["country"]
    assert response_json["city"] == fake_address["city"]
    assert response_json["address_line_1"] == fake_address["address_line_1"]
    assert response_json["address_line_2"] == fake_address["address_line_2"]
    assert response_json["post_code"] == fake_address["post_code"]
    assert response_json["actor"] is not None


async def test_create_address_missing_field(async_client: AsyncClient):
    """Fail to create an address with missing field."""
    fake = Faker()
    address = {"name": fake.name()}
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/addresses/", json=address
    )
    # TODO: improve error message
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_create_address_too_many_fields(
    async_client: AsyncClient, fake_address: dict[str, Any], seed_actors: bool
):
    """Fail to create an address with too many field."""
    print("SEED ACTORS", seed_actors)
    fake_address["new_field_1"] = "new_field_1"
    fake_address["new_field_2"] = "new_field_2"
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/addresses/", json=fake_address
    )
    assert response.status_code == status.HTTP_201_CREATED


async def test_get_address(
    async_client: AsyncClient, fake_address: dict[str, Any], seed_actors: bool
):
    """Successfully retrieve an address."""
    print("SEED ACTORS", seed_actors)
    # TODO: populate database with addresses instead of creating them one by one
    address_created = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/addresses/", json=fake_address
    )
    address_id = address_created.json()["id"]
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/addresses/{address_id}"
    )

    assert response.status_code == status.HTTP_200_OK


async def test_get_address_not_found(async_client: AsyncClient):
    """When an address is not found."""
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/addresses/{99999}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("fake_addresses", [0, 1, 5], indirect=True)
async def test_get_addresses(
    async_client: AsyncClient, fake_addresses: list[dict[str, Any]], seed_actors: bool
):
    """Get list of addresses for 0, 1 and many addresses."""
    print("SEED ACTORS", seed_actors)
    # TODO: populate database with addresses instead of creating them one by one
    # create addresses
    for address in fake_addresses:
        await async_client.post(
            f"{get_settings().API_ROOT_PATH}/addresses/", json=address
        )

    # get addresses
    response = await async_client.get(f"{get_settings().API_ROOT_PATH}/addresses/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == len(fake_addresses)
    if len(fake_addresses) > 0:
        assert response.json()["addresses"][0]["actor"] is None


@pytest.mark.parametrize("fake_addresses", [11], indirect=True)
async def test_get_addresses_with_pagination(
    async_client: AsyncClient, fake_addresses: list[dict[str, Any]], seed_actors: bool
):
    """Get list of addresses for 0, 1 and many addresses."""
    print("SEED ACTORS", seed_actors)
    # TODO: populate database with addresses instead of creating them one by one
    # create addresses
    for address in fake_addresses:
        await async_client.post(
            f"{get_settings().API_ROOT_PATH}/addresses/", json=address
        )

    # get addresses
    page_size = 10
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/addresses/", params={"page_size": page_size}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == len(fake_addresses)

    # get addresses
    page_size = 10
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/addresses/", params={"page_size": page_size}
    )
    response = await async_client.get(f"{get_settings().API_ROOT_PATH}/addresses/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == len(fake_addresses)
    assert len(response.json()["addresses"]) == page_size
