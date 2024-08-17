from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.api.main import app
from app.core.config import Settings


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def session() -> Generator[Session, None, None]:
    settings = Settings()
    engine = create_engine(settings.DATABASE_URL)

    with Session(engine) as session:
        SQLModel.metadata.create_all(engine)

        yield session

        # SQLModel.metadata.drop_all(engine)
