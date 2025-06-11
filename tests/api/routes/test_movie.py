from typing import Any

import pytest
from faker import Faker
from fastapi import status
from httpx import AsyncClient

from app.core.config import get_settings
from app.models import Actor, Movie
from app.schemas import MovieResponseDetailed

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture
def fake_movie() -> dict[str, Any]:
    """
    Provides a fake movie dictionary for testing.

    Returns:
        dict[str, Any]: A dictionary with random movie fields.
    """
    fake = Faker()
    return {
        "title": fake.street_name(),
        "year": fake.random_int(min=1920, max=2025),
        "rating": fake.random_int(min=0, max=5),
    }


@pytest.mark.parametrize(
    "actors_list, expected_count",  # noqa: PT006
    [
        ([], 0),  # no actors
        ([1], 1),  # 1 actor
        ([1, 2, 3], 3),  # many actors
    ],
)
async def test_create_movie(
    async_client: AsyncClient,
    fake_movie: dict[str, Any],
    seed_actors: list[Actor],
    actors_list: list[int],
    expected_count: int,
):
    """
    Test creating a movie with different numbers of actors.

    Args:
        async_client (AsyncClient): The HTTPX async client.
        fake_movie (dict[str, Any]): The fake movie data.
        seed_actors (list[Actor]): List of seeded actors.
        actors_list (list[int]): List of actor IDs to associate.
        expected_count (int): Expected number of actors in the response.

    Asserts:
        - Status code is 201 CREATED.
        - Response contains correct movie fields and actor count.
    """
    print(f"seed_actors: {len(seed_actors)}")
    fake_movie["actors"] = actors_list
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/movies/", json=fake_movie
    )
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()
    assert response_json["title"] == fake_movie["title"]
    assert response_json["year"] == fake_movie["year"]
    assert response_json["rating"] == fake_movie["rating"]
    assert len(response_json["actors"]) == expected_count


async def test_create_movie_missing_field(async_client: AsyncClient):
    """
    Test failure to create a movie with a missing field.

    Args:
        async_client (AsyncClient): The HTTPX async client.

    Asserts:
        - Status code is 422 UNPROCESSABLE ENTITY.
    """
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
    """
    Test creating a movie with extra fields (should ignore extras).

    Args:
        async_client (AsyncClient): The HTTPX async client.
        fake_movie (dict[str, Any]): The fake movie data.

    Asserts:
        - Status code is 201 CREATED.
    """
    fake_movie["new_field_1"] = "new_field_1"
    fake_movie["new_field_2"] = "new_field_2"
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/movies/", json=fake_movie
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "movie_index, expected_actors_count",  # noqa: PT006
    [
        (-1, 0),  # no actors
        (1, 1),  # 1 actor
        (0, 3),  # many actors
    ],
)
async def test_get_movie(
    async_client: AsyncClient,
    seed_movies: list[Movie],
    movie_index: int,
    expected_actors_count: int,
):
    """
    Test successfully retrieving a movie by ID.

    Args:
        async_client (AsyncClient): The HTTPX async client.
        seed_movies (list[Movie]): List of seeded movies.
        movie_index (int): Index of the movie to retrieve.
        expected_actors_count (int): Expected number of actors in the movie.

    Asserts:
        - Status code is 200 OK.
        - Response contains correct movie ID and actor count.
    """
    print(f"seed_movies: {len(seed_movies)}")
    movie = seed_movies[movie_index]
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/movies/{movie.id}"
    )
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_json["id"] == movie.id
    assert len(response_json["actors"]) == expected_actors_count


async def test_get_movie_not_found(async_client: AsyncClient):
    """
    Test retrieving a non-existent movie returns 404.

    Args:
        async_client (AsyncClient): The HTTPX async client.

    Asserts:
        - Status code is 404 NOT FOUND.
    """
    response = await async_client.get(f"{get_settings().API_ROOT_PATH}/movies/{99999}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("seed_movies", [0, 1, 5], indirect=True)
async def test_get_movies(async_client: AsyncClient, seed_movies: list[Movie]):
    """
    Test retrieving a list of movies for 0, 1, and many movies.

    Args:
        async_client (AsyncClient): The HTTPX async client.
        seed_movies (list[Movie]): List of seeded movies.

    Asserts:
        - Status code is 200 OK.
        - Response contains correct total and page size.
        - Actors list is empty for each movie.
    """
    print(f"seed_movies: {len(seed_movies)}")
    actors_list_len = 0

    # no params
    response = await async_client.get(f"{get_settings().API_ROOT_PATH}/movies/")
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_json["total"] == len(seed_movies)
    if len(seed_movies) > 0:
        assert len(response_json["movies"][0]["actors"]) == actors_list_len
        assert MovieResponseDetailed(**response_json["movies"][0])

    # set page size
    page_size = 1
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/movies/", params={"page_size": page_size}
    )
    response_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_json["total"] == len(seed_movies)
    assert response_json["page_size"] == page_size
    if len(seed_movies) > 0:
        assert len(response_json["movies"][0]["actors"]) == actors_list_len
        assert len(response_json["movies"]) == page_size
        assert MovieResponseDetailed(**response_json["movies"][0])


async def test_get_movies_wrong_page_values(
    async_client: AsyncClient, seed_movies: list[Movie]
):
    """
    Test validation for wrong page size parameter when getting movies.

    Args:
        async_client (AsyncClient): The HTTPX async client.
        seed_movies (list[Movie]): List of seeded movies.

    Asserts:
        - Status code is 422 UNPROCESSABLE ENTITY for invalid page size.
    """
    print(f"seed_actors: {len(seed_movies)}")
    # page size is 0
    page_size = 0
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/movies/", params={"page_size": page_size}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
