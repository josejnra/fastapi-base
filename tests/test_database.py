import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Actor

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_create_actor_database(db_session: AsyncSession):
    actor_1 = Actor(name="John Doe", age=42)
    actor_2 = Actor(name="Jane Doe", age=36)

    db_session.add(actor_1)
    db_session.add(actor_2)
    await db_session.commit()

    statement = select(Actor)
    result = await db_session.exec(statement.where(Actor.name == "John Doe"))
    actor = result.first()
    if actor:
        assert actor.name == "John Doe"
    else:
        pytest.fail("Actor not found")

    result = await db_session.exec(select(Actor))
    actors = result.all()
    total_actors = 2
    assert total_actors == len(actors)
