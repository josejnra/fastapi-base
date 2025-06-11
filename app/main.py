import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from slowapi import _rate_limit_exceeded_handler  # noqa: PLC2701
from slowapi.errors import RateLimitExceeded
from starlette.middleware import Middleware

from app.api import main
from app.core.config import get_settings
from app.core.database import init_db
from app.core.limiter import (
    RateLimitMiddleware,
    limiter,
    redis_user_rate_limiter_factory,
)
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
    """
    Runs Alembic migrations to upgrade the database schema to the latest version.

    This function configures Alembic using the migration script location and
    executes the upgrade command in a separate thread.

    Returns:
        None
    """
    logger.info("Running migrations")
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "app/migrations")
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")


@logger.catch
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, None]:  # noqa: ARG001
    """
    Context manager for FastAPI application lifespan events.

    Runs database initialization or migrations before the application starts,
    and logs shutdown information after the application stops.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None

    Returns:
        AsyncGenerator[Any, None]: The application context.
    """
    # applying migrations implies using a schema, which sqlite doesn't support
    if get_settings().is_sqlite_database():
        await init_db()
    else:
        await run_migrations()

    yield

    logger.info("Shutting down application...")


@logger.catch
def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application instance.

    Sets up CORS, GZip, and custom rate limiting middleware, configures API docs,
    adds exception handlers, instruments the app for telemetry, and includes routers.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """
    # CORS (Cross-Origin Resource Sharing)
    origins = [
        "http://localhost.tiangolo.com",
        "https://localhost.tiangolo.com",
        "http://localhost",
        "http://localhost:8080",
        "*",  # allow all origins
    ]

    middlewares = [
        Middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        # compresses responses
        # Handles GZip responses for any request that includes "gzip" in the Accept-Encoding header
        Middleware(GZipMiddleware, minimum_size=1000, compresslevel=5),
        # redis's rate limiter, based on username
        Middleware(
            RateLimitMiddleware,
            rate_limiter_factory=redis_user_rate_limiter_factory,
        ),
    ]

    app = FastAPI(
        title="Base code for FastAPI projects",
        description="My FastAPI description",
        openapi_url="/docs/openapi.json",
        docs_url="/docs",  # interactive API documentation
        redoc_url="/redoc",  # alternative automatic interactive API documentation
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
        middleware=middlewares,
    )

    # slowapi, based on ip address
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

    # instrument the app
    FastAPIInstrumentor.instrument_app(app)

    # add routers
    app.include_router(main.api_router, prefix=get_settings().API_ROOT_PATH)
    return app


app = create_app()


@app.get("/", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def root(request: Request, response: Response):  # noqa: ARG001
    """
    Root endpoint for the API.

    Returns a simple message indicating the API is live.

    Args:
        request (Request): The incoming HTTP request.
        response (Response): The outgoing HTTP response.

    Returns:
        dict: A message indicating the API is live.
    """
    return {"message": "The API is LIVE!!"}


@app.get("/health", status_code=status.HTTP_200_OK)
async def health():
    """
    Health check endpoint for the API.

    Increments a custom metric and returns a message indicating the API is live.

    Returns:
        dict: A message indicating the API is live.
    """
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
