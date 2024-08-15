from functools import lru_cache

from fastapi import Depends, FastAPI
from sqlalchemy.engine.base import Engine
from sqlmodel import Session, select

from .database import create_db_and_tables, get_engine
from .models import Actor, ActorMovie, Address, Movie
from .settings import Settings


@lru_cache
def get_settings() -> Settings:
    """settings object will be created only once, the first time it's called

    Returns:
        Settings: settings object created
    """
    settings = Settings()
    return settings


@lru_cache
def engine() -> Engine:
    """all objects will be created only once, the first time it's called

    Returns:
        tuple[Engine, Settings]: engine and settings created
    """
    settings = get_settings()
    engine = get_engine(settings.database_url)
    create_db_and_tables(engine)

    return engine


def get_db_session():
    with Session(engine()) as session:
        yield session


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


@app.get("/actors", response_model=list[Actor])
def get_actors(session: Session = Depends(get_db_session)):
    actors = session.exec(select(Actor)).all()
    return actors


@app.post("/actors", response_model=Actor)
def create_actor(actor: Actor, session: Session = Depends(get_db_session)):
    session.add(actor)
    session.commit()
    session.refresh(actor)
    return actor
