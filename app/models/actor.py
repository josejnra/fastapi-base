from datetime import datetime

from sqlalchemy import Column, func
from sqlmodel import DateTime, Field, Relationship

from .actor_movie import ActorMovie
from .address import Address
from .base import Base


class ActorBase(Base):
    name: str
    age: int


class Actor(ActorBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    movie_links: list[ActorMovie] = Relationship(back_populates="actor")

    # `joined` is used which performs an SQL JOIN to load the related addresses objects.
    # This means all data is loaded in one go.
    # It results in fewer database round-trips, but the initial load might be slower due to the join operation.
    addresses: list[Address] = Relationship(
        back_populates="actor", sa_relationship_kwargs={"lazy": "selectin"}
    )
