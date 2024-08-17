from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        env_ignore_empty=True,
        extra="ignore",
    )

    DATABASE_URL: str = "sqlite:///:memory:"
    DEBUG: bool = True
