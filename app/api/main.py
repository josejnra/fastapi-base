from functools import lru_cache
from typing import Generator

from fastapi import Depends, FastAPI
from sqlalchemy.engine.base import Engine
from sqlmodel import Session, select

from app.core.config import Settings
from app.core.database import get_engine, init_db
from app.models import (  # noqa: F401  # needed for sqlmodel in order to create tables
    Actor,
    ActorMovie,
    Address,
    Movie,
)


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
    engine = get_engine(settings.DATABASE_URL)
    init_db(engine)

    return engine


def get_db_session() -> Generator[Session, None, None]:
    with Session(engine()) as session:
        yield session


app = FastAPI(
    title="Base code for FastAPI projects",
    description="My FastAPI description",
    openapi_url="/docs/openapi.json",
    docs_url="/docs",  # interactive API documentation
    redoc_url="/redoc",  # alternative automatic interactive API documentation
    root_path="/api/v1",
)


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
