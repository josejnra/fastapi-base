from functools import lru_cache
from typing import Annotated, cast

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.core.logger import logger
from app.core.telemetry import tracer


@lru_cache
def get_engine() -> AsyncEngine:
    """
    Returns a cached SQLAlchemy AsyncEngine instance for the configured database.

    This function creates and returns an asynchronous SQLAlchemy engine using the database URL
    and debug settings from the application configuration. The engine is cached to avoid
    unnecessary re-creation and to maintain a pool of database connections.

    Returns:
        AsyncEngine: An asynchronous SQLAlchemy engine instance.
    """
    settings = get_settings()
    db_url = settings.DATABASE

    logger.debug(f"Connecting to database: {db_url} using schema: {settings.SCHEMA}")

    return create_async_engine(url=cast(str, db_url), echo=settings.DB_DEBUG)


async def init_db():
    """
    Initializes the database schema and tables if they do not exist.

    This function connects to the database using the engine and creates the schema (if not using SQLite)
    and all tables registered in the SQLModel metadata. For databases that support schemas, it ensures
    the schema exists before creating tables.

    Returns:
        None
    """
    logger.info("Initializing database")
    engine = get_engine()
    async with engine.begin() as conn:
        # SQLite does not support schema creation
        if not get_settings().is_sqlite_database():
            schema = get_settings().SCHEMA
            SQLModel.metadata.schema = schema
            logger.debug(f"Creating schema: {schema}")
            await conn.execute(CreateSchema(schema, if_not_exists=True))

        await conn.run_sync(SQLModel.metadata.create_all)


@tracer.start_as_current_span("getting db session")
async def get_db_session() -> AsyncSession:
    """
    Provides an asynchronous database session for use in dependency injection.

    This function creates and returns an AsyncSession instance using the cached engine.
    The session is configured with expire_on_commit=False to prevent attribute expiration
    after commit, which is useful for async workflows.
    Object that establishes all conversations with the database and represents
    a "holding zone" for all the objects which you've loaded or associated with it during its lifespan.

    Returns:
        AsyncSession: An asynchronous SQLAlchemy session instance.
    """
    engine = get_engine()

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore
    return cast(AsyncSession, async_session())


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
