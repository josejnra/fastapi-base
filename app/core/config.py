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

    def is_sqlite_database(self) -> bool:
        return "sqlite" in self.DATABASE_URL

    @computed_field
    def DATABASE_SCHEMA(self) -> str:
        """Set database schema name.
            If database is sqlite, then schema name is empty.

        Returns:
            str: schema name
        """
        return "" if self.is_sqlite_database() else "myapp"


@lru_cache
def get_settings() -> Settings:
    """settings object will be created only once, the first time it's called

    Returns:
        Settings: settings object created
    """
    return Settings()
