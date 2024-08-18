from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        env_ignore_empty=True,
        extra="ignore",
    )

    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    # DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost/postgres"
    DATABASE_SCHEMA: str = "myapp"
    DB_DEBUG: bool = True
    API_ROOT_PATH: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    """settings object will be created only once, the first time it's called

    Returns:
        Settings: settings object created
    """
    return Settings()
