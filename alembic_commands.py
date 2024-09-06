"""
steps to run this script:
- docker compose up -d
- update __main__ accordingly
- python alembic_commands.py
"""

import os

from alembic import command
from alembic.config import Config

os.environ["APP_DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@localhost/postgres"
)


def get_alembic_config():
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "app/migrations")
    alembic_cfg.set_main_option(
        "file_template", "%%(year)d-%%(month).2d-%%(day).2d_%%(slug)s"
    )
    return alembic_cfg


def new_revision(msg: str):
    command.revision(get_alembic_config(), message=msg, autogenerate=True)


def downgrade_revision(revision: str):
    command.downgrade(get_alembic_config(), revision)


if __name__ == "__main__":
    message = "adds user table"
    new_revision(message)
