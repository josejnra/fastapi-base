from typing import Any

import pytest
from faker import Faker
from fastapi import status
from httpx import AsyncClient

from app.core.config import get_settings

# make all test mark with `asyncio`
pytestmark = pytest.mark.asyncio


@pytest.fixture
def fake_movie() -> dict[str, Any]:
    fake = Faker()

    return {
        "title": fake.street_name(),
        "year": fake.random_int(min=1920, max=2025),
        "rating": fake.random_int(min=0, max=5),
    }


@pytest.fixture
def fake_movies(request: pytest.FixtureRequest) -> list[dict[str, Any]]:
    n = request.param
    fake = Faker()
    movies = [
        {
            "title": fake.street_name(),
            "year": fake.random_int(min=1920, max=2025),
            "rating": fake.random_int(min=0, max=5),
        }
        for _ in range(n)
    ]
    return movies


async def test_create_movie_success(
    async_client: AsyncClient, fake_movie: dict[str, Any]
):
    """Movie is created successfully."""
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/movies/", json=fake_movie
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()
    assert response_json["title"] == fake_movie["title"]
    assert response_json["year"] == fake_movie["year"]
    assert response_json["rating"] == fake_movie["rating"]


async def test_create_movie_missing_field(async_client: AsyncClient):
    """Fail to create an movie with missing field."""
    fake = Faker()
    movie = {"name": fake.name()}
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/movies/", json=movie
    )
    # TODO: improve error message
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_create_movie_too_many_fields(
    async_client: AsyncClient, fake_movie: dict[str, Any]
):
    """Fail to create an movie with too many field."""
    fake_movie["new_field_1"] = "new_field_1"
    fake_movie["new_field_2"] = "new_field_2"
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/movies/", json=fake_movie
    )
    assert response.status_code == status.HTTP_201_CREATED


async def test_get_movie(async_client: AsyncClient, fake_movie: dict[str, Any]):
    """Successfully retrieve an movie."""
    # TODO: populate database with movies instead of creating them one by one
    movie_created = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/movies/", json=fake_movie
    )
    movie_id = movie_created.json()["id"]
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/movies/{movie_id}"
    )
    assert response.status_code == status.HTTP_200_OK


async def test_get_movie_not_found(async_client: AsyncClient):
    """When an movie is not found."""
    response = await async_client.get(f"{get_settings().API_ROOT_PATH}/movies/{99999}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("fake_movies", [0, 1, 5], indirect=True)
async def test_get_movies(async_client: AsyncClient, fake_movies: list[dict[str, Any]]):
    """Get list of movies for 0, 1 and many movies."""
    # TODO: populate database with movies instead of creating them one by one
    # create movies
    for movie in fake_movies:
        await async_client.post(f"{get_settings().API_ROOT_PATH}/movies/", json=movie)

    # get movies
    response = await async_client.get(f"{get_settings().API_ROOT_PATH}/movies/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == len(fake_movies)


@pytest.mark.parametrize("fake_movies", [11], indirect=True)
async def test_get_movies_with_pagination(
    async_client: AsyncClient, fake_movies: list[dict[str, Any]]
):
    """Get list of movies for 0, 1 and many movies."""
    # TODO: populate database with movies instead of creating them one by one
    # create movies
    for movie in fake_movies:
        await async_client.post(f"{get_settings().API_ROOT_PATH}/movies/", json=movie)

    # get movies
    page_size = 10
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/movies/", params={"page_size": page_size}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == len(fake_movies)

    # get movies
    page_size = 10
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/movies/", params={"page_size": page_size}
    )
    response = await async_client.get(f"{get_settings().API_ROOT_PATH}/movies/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == len(fake_movies)
    assert len(response.json()["movies"]) == page_size
