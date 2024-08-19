from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.core.config import get_settings

from .base import Base

# in order to avoid circular imports
if TYPE_CHECKING:
    from .actor import Actor
    from .movie import Movie


class ActorMovie(Base, table=True):
    actor_id: int | None = Field(
        default=None,
        foreign_key=f"{get_settings().DATABASE_SCHEMA}.actor.id",
        primary_key=True,
    )
    movie_id: int | None = Field(
        default=None,
        foreign_key=f"{get_settings().DATABASE_SCHEMA}.movie.id",
        primary_key=True,
    )

    actor: "Actor" = Relationship(
        back_populates="movie_links", sa_relationship_kwargs={"lazy": "selectin"}
    )
    movie: "Movie" = Relationship(
        back_populates="actor_links", sa_relationship_kwargs={"lazy": "selectin"}
    )
