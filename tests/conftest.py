from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from api.app import app
from api.settings import Settings


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def session() -> Generator[Session, None, None]:
    settings = Settings()
    engine = create_engine(settings.database_url)
    # engine = create_engine("sqlite:///database.db")

    with Session(engine) as session:
        SQLModel.metadata.create_all(engine)

        yield session

        # SQLModel.metadata.drop_all(engine)
