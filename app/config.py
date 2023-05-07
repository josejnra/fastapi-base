from fastapi import FastAPI
from starlette.config import Config
from pydantic import AnyUrl, BaseSettings, PostgresDsn


config = Config(".env")  # parse .env file for env variables

ENVIRONMENT = config("ENVIRONMENT")  # get current env name
SHOW_DOCS_ENVIRONMENT = ("local", "staging")  # explicit list of allowed envs

app_configs = {"title": "My Cool API"}
if ENVIRONMENT not in SHOW_DOCS_ENVIRONMENT:
    app_configs["openapi_url"] = None  # set url for docs as null

app = FastAPI(**app_configs)


class AppSettings(BaseSettings):

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "app_"

    DATABASE_URL: PostgresDsn
    IS_GOOD_ENV: bool = True
    ALLOWED_CORS_ORIGINS: set[AnyUrl]
