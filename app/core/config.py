from functools import lru_cache
from typing import ClassVar, cast

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        env_ignore_empty=True,
        extra="ignore",
    )

    database_class: ClassVar[str | None] = None
    database_schema_class: ClassVar[str | None] = None
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///:memory:",
        description="Database async connection URL",
    )
    DATABASE_SCHEMA: str | None = Field(
        default=None, description="database schema name"
    )
    DB_DEBUG: bool = False
    LOG_LEVEL: str = "TRACE"
    API_ROOT_PATH: str = "/api/v1"

    @computed_field()
    def DATABASE(self) -> str:
        """Define database name based on the following priority:
            1. database_class - class variable
            2. DATABASE_URL - environment variable or passed value
            3. default - sqlitedb

        Returns:
            str: schema name
        """
        if Settings.database_class is not None:
            return Settings.database_class
        else:
            Settings.database_class = self.DATABASE_URL
            return self.DATABASE_URL

    def is_sqlite_database(self) -> bool:
        return "sqlite" in cast(str, self.DATABASE)

    @computed_field()
    def SCHEMA(self) -> str:
        """Define database schema name based on the following priority:
            1. database_schema_class - class variable
            2. DATABASE_SCHEMA - environment variable or passed value
            3. sqlite database - for sqlite database, schema name is empty
            4. default - myapp

        Returns:
            str: schema name
        """
        if Settings.database_schema_class not in {None, ""}:
            return cast(str, Settings.database_schema_class)
        elif self.DATABASE_SCHEMA is not None:
            Settings.database_schema_class = self.DATABASE_SCHEMA
            return self.DATABASE_SCHEMA
        elif self.is_sqlite_database():
            schema = ""
            Settings.database_schema_class = schema
            return schema
        else:
            schema = "myapp"
            Settings.database_schema_class = schema
            return schema


@lru_cache
def get_settings() -> Settings:
    """settings object will be created only once, the first time it's called

    Returns:
        Settings: settings object created
    """
    return Settings()
