from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, func
from sqlmodel import DateTime, Field, Relationship

from app.core.config import get_settings

from .base import Base

# in order to avoid circular imports
if TYPE_CHECKING:
    from .actor import Actor


class AddressBase(Base):
    country: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=255)
    address_line_1: str = Field(min_length=1, max_length=255)
    address_line_2: str | None = Field(default=None, min_length=1, max_length=255)
    post_code: str = Field(min_length=1, max_length=15)


class Address(AddressBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    actor_id: int = Field(
        nullable=False,
        foreign_key=f"{get_settings().SCHEMA}.actor.id",
        ondelete="CASCADE",
    )

    # `selectin` strategy breaks up the loading into two separate queries -
    # one for the parent and one for the child objects.
    # This can sometimes be faster than joinedload as it avoids complex joins.
    actor: "Actor" = Relationship(
        back_populates="addresses",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
