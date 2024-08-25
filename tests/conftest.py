from typing import AsyncGenerator, Callable

import pytest
import pytest_asyncio
from faker import Faker
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis, from_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.main import app
from app.models import Actor, ActorMovie, Address, Movie


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore

    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.drop_all)
        await connection.run_sync(SQLModel.metadata.create_all)
        async with async_session(bind=connection) as session:
            yield session
            await session.flush()
            await session.rollback()


@pytest.fixture
def override_get_db(db_session: AsyncSession) -> Callable:
    async def _override_get_db():
        yield db_session

    return _override_get_db


@pytest.fixture
def test_app(override_get_db: Callable) -> FastAPI:
    app.dependency_overrides[get_db_session] = override_get_db

    return app


@pytest_asyncio.fixture
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(test_app),  # type: ignore
        base_url="http://test",
        timeout=None,
    ) as ac:
        yield ac


@pytest.fixture
async def seed_actors(
    request: pytest.FixtureRequest, db_session: AsyncSession
) -> list[Actor]:
    """Fixture to seed actors.

    Args:
        request (pytest.FixtureRequest): number of actors to create, defaults to 3.
        db_session (AsyncSession): database session

    Returns:
        list[Actor]: list of actors
    """
    n = getattr(request, "param", 3)
    fake = Faker()
    actors = [
        Actor(id=i, name=fake.name(), age=fake.random_int(min=10, max=90))
        for i in range(1, n + 1)
    ]
    db_session.add_all(actors)
    await db_session.commit()
    for actor in actors:
        await db_session.refresh(actor)

    return actors


@pytest.fixture
async def seed_addresses(
    db_session: AsyncSession, seed_actors: list[Actor]
) -> list[Address]:
    """Fixture to seed addresses."""
    fake = Faker()
    min_actors = 2
    if len(seed_actors) < min_actors:
        raise ValueError("number of actors must be >= 2")

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
        for i, actor in enumerate(seed_actors)
    ]

    # add one more address for first actor in the list
    addresses.append(
        Address(
            id=len(addresses) + 1,
            actor=seed_actors[0],
            country=fake.country(),
            city=fake.city(),
            post_code=fake.postcode(),
            address_line_1=fake.address(),
            actor_id=seed_actors[0].id,
        )
    )
    db_session.add_all(addresses)
    await db_session.commit()
    for address in addresses:
        await db_session.refresh(address)
    return addresses


@pytest.fixture
async def seed_movies(
    request: pytest.FixtureRequest, db_session: AsyncSession, seed_actors: list[Actor]
) -> list[Movie]:
    """Fixture to seed movies.
    Args:
        request (pytest.FixtureRequest): number of movies to create, defaults to 4. Must be >= 2
        db_session (AsyncSession): database session
        seed_actors (list[Actor]): list of actors to use

    Returns:
        list[Movie]: list of movies.
            when n = 1: list of 1 movie with 1 actor
            when n>= 2: First movie has actors 1, 2, 3, last one has no actors.
    """
    n = getattr(request, "param", 4)
    fake = Faker()

    if n == 0:
        return []
    elif n == 1:
        movie = Movie(
            id=1,
            title=fake.sentence(),
            year=int(fake.year()),
            rating=fake.random_int(min=1, max=5),
        )
        db_session.add(movie)
        await db_session.commit()
        await db_session.refresh(movie)

        actor_movie = ActorMovie(actor=seed_actors[0], movie=movie)
        db_session.add(actor_movie)
        await db_session.commit()

        return [movie]
    else:
        movies = [
            Movie(
                id=i,
                title=fake.sentence(),
                year=int(fake.year()),
                rating=fake.random_int(min=1, max=5),
            )
            for i in range(1, n + 1)
        ]

        db_session.add_all(movies)
        await db_session.commit()
        for movie in movies:
            await db_session.refresh(movie)

        # adds 1 actor per movie, except for the last one
        actor_movies = [
            ActorMovie(actor=seed_actors[0], movie=movie) for movie in movies[:-1]
        ]

        # first movie has actors 1, 2, 3
        actor_movies.extend([
            ActorMovie(actor=seed_actors[1], movie=movies[0]),
            ActorMovie(actor=seed_actors[2], movie=movies[0]),
        ])

        db_session.add_all(actor_movies)
        await db_session.commit()
        return movies


@pytest.fixture
def redis_client() -> Redis:
    return from_url(get_settings().REDIS_URL)
