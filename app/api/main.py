from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import Depends, FastAPI
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session, init_db
from app.models import (  # noqa: F401  # needed for sqlmodel in order to create tables
    Actor,
    ActorMovie,
    Address,
    Movie,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, None]:  # noqa: ARG001
    """Run tasks before and after the server starts.

    Args:
        app (FastAPI): implicit FastAPI application

    Returns:
        AsyncGenerator[Any, None]: application
    """
    await init_db()

    yield


def create_app() -> FastAPI:
    """Create FastAPI application.

    Returns:
        FastAPI: FastAPI application
    """
    app = FastAPI(
        title="Base code for FastAPI projects",
        description="My FastAPI description",
        openapi_url="/docs/openapi.json",
        docs_url="/docs",  # interactive API documentation
        redoc_url="/redoc",  # alternative automatic interactive API documentation
        root_path=get_settings().API_ROOT_PATH,
        lifespan=lifespan,
    )

    return app


app = create_app()


@app.get("/")
async def read_root():
    return {"Hello": "World"}
    # return RedirectResponse(url="/docs")


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


@app.post("/actors", response_model=Actor)
async def create_actor(actor: Actor, session: AsyncSession = Depends(get_db_session)):
    session.add(actor)
    await session.commit()
    await session.refresh(actor)
    return actor


@app.get("/actors", response_model=list[Actor])
async def get_actors(session: AsyncSession = Depends(get_db_session)):
    result = await session.exec(select(Actor))
    actors = result.all()
    return actors
