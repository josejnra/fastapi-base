import secrets

import pytest
from httpx import AsyncClient
from starlette import status

from app.core.config import get_settings
from app.models import User

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


async def test_generate_token(seed_users: list[User], async_client: AsyncClient):
    """
    Test generating a JWT token and authenticating a user.

    Args:
        seed_users (list[User]): List of seeded users.
        async_client (AsyncClient): The HTTPX async client.

    Asserts:
        - Token is generated and returned in the response.
        - Token can be used to authenticate and access the /auth/me endpoint.
    """
    print("users added: ", len(seed_users))
    user = {
        "username": seed_users[0].username,
        "password": "123",
    }
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/auth/token", data=user
    )
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response_json
    assert "token_type" in response_json

    # validate token
    header = {"Authorization": f"Bearer {response_json['access_token']}"}
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/auth/me", headers=header
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == f"User {seed_users[0].username} authenticated"


async def test_incorrect_token(async_client: AsyncClient):
    """
    Test fails using an incorrect token.

    Args:
        async_client (AsyncClient): The HTTPX async client.

    Asserts:
        - Status code is 401 UNAUTHORIZED.
    """
    header = {"Authorization": f"Bearer {secrets.token_hex(32)}"}
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/auth/me", headers=header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_incorrect_password(seed_users: list[User], async_client: AsyncClient):
    """
    Test fails to generate token with incorrect password.

    Args:
        seed_users (list[User]): List of seeded users.
        async_client (AsyncClient): The HTTPX async client.

    Asserts:
        - Status code is 400 BAD REQUEST.
    """
    print("users added: ", len(seed_users))
    user = {
        "username": seed_users[0].username,
        "password": "123544332",
    }
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/auth/token", data=user
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_incorrect_username(seed_users: list[User], async_client: AsyncClient):
    """
    Test fails to generate token with incorrect username.

    Args:
        seed_users (list[User]): List of seeded users.
        async_client (AsyncClient): The HTTPX async client.

    Asserts:
        - Status code is 404 NOT FOUND.
    """
    print("users added: ", len(seed_users))
    user = {
        "username": "random-username",
        "password": "123",
    }
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/auth/token", data=user
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
