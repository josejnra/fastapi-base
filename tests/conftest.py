from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.main import app
from app.core.database import get_engine


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)  # type: ignore

    async with async_session() as session:
        yield session
