from datetime import datetime

from pydantic import EmailStr
from sqlalchemy import Column, String, func
from sqlmodel import DateTime, Field

from .base import Base


class UserBase(Base):
    name: str = Field(min_length=1, max_length=255)
    username: str = Field(
        min_length=1, max_length=255, sa_column=Column("username", String, unique=True)
    )
    email: EmailStr


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    password: str
    disabled: bool = Field(default=False)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )
