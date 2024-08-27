from functools import lru_cache
from typing import AsyncGenerator, cast

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
    """Get SQLAlchemy engine from database URL.

    Returns:
        AsyncEngine: object that handles the communication with the database.
        Maintains a pool of database connections.
    """
    settings = get_settings()
    db_url = settings.DATABASE

    logger.debug(f"Connecting to database: {db_url} using schema: {settings.SCHEMA}")

    return create_async_engine(url=cast(str, db_url), echo=settings.DB_DEBUG)


async def init_db():
    """It takes an engine and uses it to create the database
    and all the tables registered in this MetaData object if not exists.

    """
    logger.info("Initializing database")
    engine = get_engine()
    async with engine.begin() as conn:
        # sqlite doesn't support schema creation
        if not get_settings().is_sqlite_database():
            schema = get_settings().SCHEMA
            SQLModel.metadata.schema = schema
            logger.debug(f"Creating schema: {schema}")
            await conn.execute(CreateSchema(schema, if_not_exists=True))

        await conn.run_sync(SQLModel.metadata.create_all)


@tracer.start_as_current_span("get_db_session")
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """It takes an engine and uses it to create a session
        that will be used to interact with the database.

    Returns:
        Generator[AsyncSession, None, None]: object that establishes all conversations with the database
        and represents a "holding zone" for all the objects which you've loaded or associated with it during its lifespan.
    """
    engine = get_engine()

    # expire_on_commit=False will prevent attributes from being expired
    # after commit.
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore

    async with async_session() as session:
        yield session
