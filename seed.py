import asyncio
import random
from typing import AsyncGenerator, cast

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import QueryableAttribute, selectinload, sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Actor, ActorMovie, Address, Movie

DB_URL = "postgresql+asyncpg://postgres:postgres@localhost/postgres"
DB_SCHEMA = "myapp"


def get_engine(db_url: str = DB_URL, schema: str = DB_SCHEMA) -> AsyncEngine:
    return create_async_engine(
        url=db_url,
        echo=False,
        execution_options={"schema_translate_map": {None: schema}},
    )


async def get_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)  # type: ignore

    async with async_session() as session:
        yield session


async def seed_data():
    engine = get_engine()

    # create actors
    fake = Faker()
    actors = [
        Actor(id=i, name=fake.name(), age=fake.random_int(min=10, max=90))
        for i in range(1, 4)
    ]
    async for session in get_session(engine):
        session.add_all(actors)
        await session.refresh(actors)
        await session.commit()

    # create addresses
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
        for i, actor in enumerate(actors)
    ]

    # add one more address for first actor in the list
    addresses.append(
        Address(
            id=len(addresses) + 1,
            actor=actors[0],
            country=fake.country(),
            city=fake.city(),
            post_code=fake.postcode(),
            address_line_1=fake.address(),
            actor_id=actors[0].id,
        )
    )
    async for session in get_session(engine):
        session.add_all(addresses)
        await session.commit()

    # create movies
    movies = [
        Movie(
            id=i,
            title=fake.sentence(),
            year=int(fake.year()),
            rating=fake.random_int(min=1, max=5),
        )
        for i in range(1, 5)
    ]

    async for session in get_session(engine):
        session.add_all(movies)
        await session.commit()

    # adds 1 actor per movie, except for the last one
    actor_movies = [
        ActorMovie(actor=actors[random.randint(0, len(actors))], movie=movie)
        for movie in movies[:-1]
    ]

    actor_movies.extend([
        ActorMovie(actor=actors[1], movie=movies[0]),
        ActorMovie(actor=actors[2], movie=movies[0]),
    ])

    async for session in get_session(engine):
        session.add_all(actor_movies)
        await session.commit()

    print("Data seeded successfully.")


async def get_actor(actor_id: int = 20):
    engine = get_engine()
    async for session in get_session(engine):
        statment = (
            select(Actor)
            .options(selectinload(cast(QueryableAttribute, Actor.addresses)))
            .where(Actor.id == actor_id)
        )
        result = await session.scalars(statment)
        actor = result.first()
        print(actor)


async def list_actors():
    engine = get_engine()
    async for session in get_session(engine):
        statement = select(Actor)
        result = await session.exec(statement)
        actors = result.all()
        print(actors)


if __name__ == "__main__":
    asyncio.run(seed_data())

    # asyncio.run(list_actors())

    # asyncio.run(get_actor())
