from datetime import datetime

from sqlalchemy import Column, func
from sqlmodel import DateTime, Field, Relationship, SQLModel

from .actor_movie import ActorMovie


class Movie(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    year: int = Field(default=1900)
    rating: int = Field(default=0, ge=0, le=5)
    created_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    actor_links: list[ActorMovie] = Relationship(back_populates="movie")
