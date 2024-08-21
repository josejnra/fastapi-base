from typing import AsyncGenerator, Callable

import pytest
import pytest_asyncio
from faker import Faker
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db_session
from app.main import app
from app.models import Actor, Address


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
    """Fixture to seed actors."""
    n = getattr(request, "param", 3)
    fake = Faker()
    actors = [
        Actor(id=i, name=fake.name(), age=fake.random_int(min=10, max=90))
        for i in range(1, n)
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
