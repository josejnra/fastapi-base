import pytest
from _pytest.monkeypatch import MonkeyPatch

from app.core.config import Settings

POSTGRES_URL = "postgresql://user:password@localhost/dbname"
DEFAULT_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def default_settings():
    return Settings()


@pytest.fixture
def custom_settings() -> Settings:
    return Settings(DATABASE_URL=POSTGRES_URL)


# def test_default_database_url(default_settings):
#     assert default_settings.DATABASE_URL == "sqlite+aiosqlite:///:memory:"


# def test_custom_database_url(custom_settings: Settings):
#     assert custom_settings.DATABASE_URL == "postgresql://user:password@localhost/dbname"


# def test_is_sqlite_database(default_settings):
#     assert default_settings.is_sqlite_database() is True


# def test_is_not_sqlite_database(custom_settings: Settings):
#     assert custom_settings.is_sqlite_database() is False


# def test_default_database_schema(default_settings):
#     assert not default_settings.DATABASE_SCHEMA


# def test_custom_database_schema(custom_settings: Settings):
#     assert custom_settings.DATABASE_SCHEMA == "myapp"


def test_schema_default(default_settings: Settings):
    assert default_settings.SCHEMA == ""  # noqa: PLC1901


def test_schema_passed():
    schema = "myschema"
    settings = Settings(DATABASE_SCHEMA=schema)
    assert settings.SCHEMA == schema


def test_schema_default_and_passed(default_settings: Settings):
    schema = "myschema"
    settings = Settings(DATABASE_SCHEMA=schema)
    assert default_settings.SCHEMA == schema
    assert settings.SCHEMA == schema


@pytest.mark.env
def test_schema_from_env(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("APP_DATABASE_SCHEMA", "myschema")
    settings = Settings()
    assert settings.SCHEMA == "myschema"


@pytest.mark.env
def test_database_from_env(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("APP_DATABASE_URL", POSTGRES_URL)
    settings = Settings()
    assert settings.DATABASE_URL == POSTGRES_URL
