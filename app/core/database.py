from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine

# from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.config import Settings


@lru_cache
def get_engine() -> AsyncEngine:
    """Get SQLAlchemy engine from database URL.

    Returns:
        Engine: object that handles the communication with the database.
    """
    settings = Settings()
    db_url = settings.DATABASE_URL
    return create_async_engine(url=db_url, echo=True)


async def init_db():
    """It takes an engine and uses it to create the database
    and all the tables registered in this MetaData object if not exists.

    """
    engine = get_engine()
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """It takes an engine and uses it to create a session
        that will be used to interact with the database.

    Returns:
        Generator[AsyncSession, None, None]: object that handles the communication with the database.
    """
    # async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    # async with async_session() as session:
    #     yield session

    # expire_on_commit=False will prevent attributes from being expired
    # after commit.

    engine = get_engine()
    # async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)  # type: ignore
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        yield session
