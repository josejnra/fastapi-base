import secrets

import pytest
from httpx import AsyncClient
from starlette import status

from app.core.config import get_settings
from app.models import User

# make all test mark with `asyncio`
pytestmark = pytest.mark.asyncio


async def test_generate_token(seed_users: list[User], async_client: AsyncClient):
    """test generate token"""
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
    """test fails using incorrect token"""
    header = {"Authorization": f"Bearer {secrets.token_hex(32)}"}
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/auth/me", headers=header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_incorrect_password(seed_users: list[User], async_client: AsyncClient):
    """test fails to generate token"""
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
    """test fails to generate token"""
    print("users added: ", len(seed_users))
    user = {
        "username": "random-username",
        "password": "123",
    }
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/auth/token", data=user
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
