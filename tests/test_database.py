from sqlmodel import Session, select

from api.models import Actor


def test_create_actor(session: Session):
    actor_1 = Actor(name="John Doe", age=42)
    actor_2 = Actor(name="Jane Doe", age=36)

    session.add(actor_1)
    session.add(actor_2)
    session.commit()

    statement = select(Actor)
    actor = session.exec(statement.where(Actor.name == "John Doe")).first()
    assert actor.name == "John Doe"

    actors = session.exec(statement).all()
    total_actors = 2
    assert total_actors == len(actors)
