from typing import Any

import pytest
from faker import Faker
from fastapi import status
from httpx import AsyncClient

from app.core.config import get_settings
from app.models import Actor, Movie
from app.schemas import MovieResponseDetailed

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


@pytest.mark.parametrize(
    "actors_list, expected_count",  # noqa: PT006
    [
        ([], 0),  # no  actors
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
    """Create movie with different number of actors for each."""
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
    """Successfully retrieve a movie."""
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
    """When an movie is not found."""
    response = await async_client.get(f"{get_settings().API_ROOT_PATH}/movies/{99999}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("seed_movies", [0, 1, 5], indirect=True)
async def test_get_movies(async_client: AsyncClient, seed_movies: list[Movie]):
    """Get list of movies for 0, 1 and many movies."""
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
    """Validate wrong param when getting movies."""
    print(f"seed_actors: {len(seed_movies)}")
    # page size is 0
    page_size = 0
    response = await async_client.get(
        f"{get_settings().API_ROOT_PATH}/movies/", params={"page_size": page_size}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
