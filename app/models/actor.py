from datetime import datetime

from sqlalchemy import Column, func
from sqlmodel import DateTime, Field, Relationship, SQLModel

from .actor_movie import ActorMovie
from .address import Address


class Actor(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    age: int
    created_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    movie_links: list[ActorMovie] = Relationship(back_populates="actor")

    addresses: list[Address] = Relationship(back_populates="actor")
