from sqlmodel import SQLModel

from app.core.config import get_settings


class Base(SQLModel, table=False):
    __table_args__ = {"schema": get_settings().SCHEMA}
