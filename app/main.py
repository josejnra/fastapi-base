import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, status

from app.api import main
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logger import logger
from app.models import (  # noqa: F401  # needed for sqlmodel in order to create tables
    Actor,
    ActorMovie,
    Address,
    Movie,
)


@logger.catch
async def run_migrations():
    logger.info("Running migrations")
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "app/migrations")
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")


@logger.catch
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, None]:  # noqa: ARG001
    """Run tasks before and after the server starts.

    Args:
        app (FastAPI): implicit FastAPI application

    Returns:
        AsyncGenerator[Any, None]: application
    """
    # applying migrations implies using a schema, which sqlite doesn't support
    if get_settings().is_sqlite_database():
        await init_db()
    else:
        await run_migrations()

    yield


@logger.catch
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
