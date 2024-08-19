import pytest
from faker import Faker
from httpx import AsyncClient

# make all test mark with `asyncio`
pytestmark = pytest.mark.asyncio


# --------------------------------
# Actor
# --------------------------------
async def test_create_actor(async_client: AsyncClient):
    """Test if the actor is created successfully."""
    fake = Faker()

    actor = {"name": fake.name(), "age": fake.random_int(min=18, max=100)}

    success_code = 201
    response = await async_client.post("/actors", json=actor)
    assert response.status_code == success_code
    response_json = response.json()
    assert response_json["name"] == actor["name"]
    assert response_json["age"] == actor["age"]
    print(response_json)


# --------------------------------
# Address
# --------------------------------
async def test_create_address(async_client: AsyncClient):
    """Test whether actor is created along with address successfully."""
    fake = Faker()

    # create actor
    actor = {"name": fake.name(), "age": fake.random_int(min=18, max=100)}

    success_code = 201
    response = await async_client.post("/actors", json=actor)
    assert response.status_code == success_code
    response_json = response.json()
    assert response_json["name"] == actor["name"]
    assert response_json["age"] == actor["age"]
