from collections.abc import AsyncGenerator, Callable

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
from app.core.security import get_password_hash
from app.main import app
from app.models import Actor, ActorMovie, Address, Movie, User


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an in-memory SQLite database session for testing.

    Yields:
        AsyncSession: An asynchronous SQLAlchemy session instance.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore

    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.drop_all)
        await connection.run_sync(SQLModel.metadata.create_all)
        session = async_session(bind=connection)
        yield session
        await session.flush()
        await session.rollback()


@pytest.fixture
def override_get_db(
    db_session: AsyncSession,
) -> Callable[[], AsyncGenerator[AsyncSession, None]]:
    """
    Provides a dependency override for the database session.

    Args:
        db_session (AsyncSession): The database session to yield.

    Returns:
        Callable: A function yielding the provided session.
    """

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    return _override_get_db


@pytest.fixture
def test_app(
    override_get_db: Callable[[], AsyncGenerator[AsyncSession, None]],
) -> FastAPI:
    """
    Provides a FastAPI app instance with overridden database dependency.

    Args:
        override_get_db (Callable): The database session override.

    Returns:
        FastAPI: The FastAPI app instance.
    """
    app.dependency_overrides[get_db_session] = override_get_db
    return app


@pytest_asyncio.fixture
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an asynchronous HTTP client for testing.

    Args:
        test_app (FastAPI): The FastAPI app instance.

    Yields:
        AsyncClient: An HTTPX asynchronous client.
    """
    async with AsyncClient(
        transport=ASGITransport(test_app),  # type: ignore
        base_url="http://test",
        timeout=None,
    ) as ac:
        yield ac


@pytest.fixture
async def seed_users(
    request: pytest.FixtureRequest, db_session: AsyncSession
) -> list[User]:
    """
    Seeds the database with users for testing.

    Args:
        request (pytest.FixtureRequest): Number of users to create, defaults to 1.
        db_session (AsyncSession): Database session.

    Returns:
        list[User]: List of created users.
    """
    n = getattr(request, "param", 1)
    fake = Faker()

    users = [
        User(
            name="admin",
            username="admin",
            email="admin@admin.com",
            password=get_password_hash("123"),
        )
    ]
    if n > 1:
        new_users = [
            User(
                name=fake.name(),
                username=fake.user_name(),
                email=fake.email(),
                password=get_password_hash(fake.password()),
            )
            for _ in range(n - 1)
        ]
        users.extend(new_users)

    db_session.add_all(users)
    await db_session.commit()
    for user in users:
        await db_session.refresh(user)

    return users


@pytest.fixture
async def auth_header(
    async_client: AsyncClient, seed_users: list[User]
) -> dict[str, str]:
    """
    Provides an authentication header for the seeded admin user.

    Args:
        async_client (AsyncClient): The HTTPX async client.
        seed_users (list[User]): List of seeded users.

    Returns:
        dict[str, str]: Authorization header with Bearer token.
    """
    user = seed_users[0]  # admin user
    login_data = {
        "username": user.username,
        "password": "123",
    }
    response = await async_client.post(
        f"{get_settings().API_ROOT_PATH}/auth/token", data=login_data
    )
    response_json = response.json()

    return {"Authorization": f"Bearer {response_json['access_token']}"}


@pytest.fixture
async def seed_actors(
    request: pytest.FixtureRequest, db_session: AsyncSession
) -> list[Actor]:
    """
    Seeds the database with actors for testing.

    Args:
        request (pytest.FixtureRequest): Number of actors to create, defaults to 3.
        db_session (AsyncSession): Database session.

    Returns:
        list[Actor]: List of created actors.
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
    """
    Seeds the database with addresses for testing.

    Args:
        db_session (AsyncSession): Database session.
        seed_actors (list[Actor]): List of actors to associate addresses with.

    Returns:
        list[Address]: List of created addresses.
    """
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
    """
    Seeds the database with movies for testing.

    Args:
        request (pytest.FixtureRequest): Number of movies to create, defaults to 4. Must be >= 2.
        db_session (AsyncSession): Database session.
        seed_actors (list[Actor]): List of actors to use.

    Returns:
        list[Movie]: List of created movies.
            When n = 1: list of 1 movie with 1 actor.
            When n >= 2: First movie has actors 1, 2, 3, last one has no actors.
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
    """
    Provides a Redis client instance for testing.

    Returns:
        Redis: An asynchronous Redis client.
    """
    redis_url = get_settings().REDIS_URL
    return from_url(redis_url)
