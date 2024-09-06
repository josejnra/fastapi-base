import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request, Response, status
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from slowapi import _rate_limit_exceeded_handler  # noqa: PLC2701
from slowapi.errors import RateLimitExceeded

from app.api import main
from app.core.config import get_settings
from app.core.database import init_db
from app.core.limiter import RateLimitMiddleware, limiter
from app.core.logger import logger
from app.core.telemetry import meter, tracer
from app.models import (  # noqa: F401  # needed for sqlmodel in order to create tables
    Actor,
    ActorMovie,
    Address,
    Movie,
    User,
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

    # slowapi, based on ip address
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

    # redis's rate limiter, based on username
    app.add_middleware(
        RateLimitMiddleware,
        rate_limit_per_minute=get_settings().RATE_LIMIT,
    )

    # instrument the app
    FastAPIInstrumentor.instrument_app(app)

    # add routers
    app.include_router(main.api_router, prefix=get_settings().API_ROOT_PATH)
    return app


app = create_app()


@app.get("/", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def root(request: Request, response: Response):  # noqa: ARG001
    return {"message": "The API is LIVE!!"}


@app.get("/health", status_code=status.HTTP_200_OK)
async def health():
    work_counter = meter.create_counter(
        name="health_call_counter",
        unit="1",
        description="Counts the number of requests to health endpoint",
    )
    work_counter.add(1)

    with tracer.start_as_current_span("building-response") as span:
        result = {"message": "The API is LIVE!!"}

        span.set_status(trace.Status(trace.StatusCode.OK))

    return result
