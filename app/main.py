from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, status

from app.api import main
from app.core.config import get_settings
from app.core.database import init_db
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
        lifespan=lifespan,
    )

    app.include_router(main.api_router, prefix=get_settings().API_ROOT_PATH)
    return app


app = create_app()


@app.get("/healthchecker", status_code=status.HTTP_200_OK)
def root():
    return {"message": "The API is LIVE!!"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
