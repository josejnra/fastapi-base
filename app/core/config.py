from functools import lru_cache

from pydantic import computed_field
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
    DB_DEBUG: bool = False
    API_ROOT_PATH: str = "/api/v1"

    @computed_field
    def DATABASE_SCHEMA(self) -> str:
        return "" if "sqlite" in self.DATABASE_URL else "myapp"


@lru_cache
def get_settings() -> Settings:
    """settings object will be created only once, the first time it's called

    Returns:
        Settings: settings object created
    """
    return Settings()
