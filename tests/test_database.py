import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Actor

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_create_actor(session: AsyncSession):
    actor_1 = Actor(name="John Doe", age=42)
    actor_2 = Actor(name="Jane Doe", age=36)

    session.add(actor_1)
    session.add(actor_2)
    await session.commit()

    statement = select(Actor)
    result = await session.execute(statement.where(Actor.name == "John Doe"))
    actor = result.scalars().first()
    if actor:
        assert actor.name == "John Doe"
    else:
        pytest.fail("Actor not found")

    result = await session.execute(statement)
    actors = result.scalars().all()
    total_actors = 2
    assert total_actors == len(actors)
