from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, func
from sqlmodel import DateTime, Field, Relationship

from app.core.config import get_settings

from .base import Base

# in order to avoid circular imports
if TYPE_CHECKING:
    from .actor import Actor


class Address(Base, table=True):
    id: int | None = Field(default=None, primary_key=True)
    country: str
    city: str
    address_line_1: str
    address_line_2: str | None = Field(default=None)
    postcode: str
    created_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    actor_id: int = Field(
        default=None, foreign_key=f"{get_settings().DATABASE_SCHEMA}.actor.id"
    )
    actor: "Actor" = Relationship(back_populates="addresses")
