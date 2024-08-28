import asyncio
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
        Actor(name=fake.name(), age=fake.random_int(min=10, max=90))
        for _ in range(1, 5)
    ]
    async for session in get_session(engine):
        session.add_all(actors)
        await session.commit()
        for actor in actors:
            await session.refresh(actor)

    # create addresses
    addresses = [
        Address(
            actor=actor,
            country=fake.country(),
            city=fake.city(),
            post_code=fake.postcode(),
            address_line_1=fake.address(),
            actor_id=actor.id,
        )
        for actor in actors
    ]

    # add one more address for first actor in the list
    addresses.append(
        Address(
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
            title=fake.sentence(),
            year=int(fake.year()),
            rating=fake.random_int(min=1, max=5),
        )
        for _ in range(1, 5)
    ]

    async for session in get_session(engine):
        session.add_all(movies)
        await session.commit()
        for movie in movies:
            await session.refresh(movie)

    # adds 1 actor per movie, except for the last one
    actor_movies = [
        ActorMovie(actor=actor, movie=movie)
        for movie, actor in zip(movies[:-1], actors[:-1])
    ]

    actor_movies.extend([ActorMovie(actor=actors[-1], movie=movies[-1])])

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
