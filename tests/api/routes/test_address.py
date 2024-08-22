from typing import Any

import pytest
from faker import Faker
from fastapi import status
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.models import Actor, Address
from app.schemas import AddressResponseDetailed

# make all test mark with `asyncio`
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def seed_addresses_by_1_actor(
    request: pytest.FixtureRequest, db_session: AsyncSession
) -> list[Address]:
    """Fixture to addresses for 1 actor."""
    count_addresses = request.param

    fake = Faker()
    actor = Actor(id=1, name=fake.name(), age=fake.random_int(min=10, max=90))
    db_session.add(actor)
    await db_session.commit()
    await db_session.refresh(actor)

    addresses = [
        Address(
            id=i,
            actor=actor,
            country=fake.country(),
            city=fake.city(),
            post_code=fake.postcode(),
            address_line_1=fake.address(),
            actor_id=actor.id,
        )
        for i in range(1, count_addresses)
    ]

    db_session.add_all(addresses)
    await db_session.commit()
    for address in addresses:
        await db_session.refresh(address)

    return addresses


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


async def test_create_address_success(
    async_client: AsyncClient, fake_address: dict[str, Any], seed_actors: list[Actor]
):
    """address is created successfully."""
    print(f"seed_actors: {len(seed_actors)}")
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
    async_client: AsyncClient, fake_address: dict[str, Any], seed_actors: list[Actor]
):
    """Fail to create an address with too many field."""
    print(f"seed_actors: {len(seed_actors)}")
    fake_address["new_field_1"] = "new_field_1"
    fake_address["new_field_2"] = "new_field_2"
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/addresses/", json=fake_address
    )
    assert response.status_code == status.HTTP_201_CREATED


async def test_get_address(async_client: AsyncClient, seed_addresses: list[Address]):
    """Successfully retrieve an address."""
    print(f"seed_actors: {len(seed_addresses)}")
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/addresses/{seed_addresses[0].id}"
    )

    assert response.status_code == status.HTTP_200_OK


async def test_get_address_not_found(async_client: AsyncClient):
    """When an address is not found."""
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/addresses/{99999}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("seed_addresses_by_1_actor", [0, 1, 5], indirect=True)
async def test_get_addresses(
    async_client: AsyncClient, seed_addresses_by_1_actor: list[Address]
):
    """Get list of addresses for 0, 1 and many addresses."""
    print(f"seed_addresses_by_1_actor: {len(seed_addresses_by_1_actor)}")

    # no params
    response = await async_client.get(f"{get_settings().API_ROOT_PATH}/addresses/")
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_json["total"] == len(seed_addresses_by_1_actor)
    if len(seed_addresses_by_1_actor) > 0:
        assert response_json["addresses"][0]["actor"] is None
        assert AddressResponseDetailed(**response_json["addresses"][0])

    # set page size
    page_size = 1
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/addresses/", params={"page_size": page_size}
    )
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == len(seed_addresses_by_1_actor)
    if len(seed_addresses_by_1_actor) > 0:
        assert len(response_json["addresses"]) == page_size
        assert AddressResponseDetailed(**response_json["addresses"][0])
