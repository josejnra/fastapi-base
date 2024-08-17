from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

# in order to avoid circular imports
if TYPE_CHECKING:
    from .actor import Actor
    from .movie import Movie


class ActorMovie(SQLModel, table=True):
    actor_id: int | None = Field(default=None, foreign_key="actor.id", primary_key=True)
    movie_id: int | None = Field(default=None, foreign_key="movie.id", primary_key=True)

    actor: "Actor" = Relationship(back_populates="movie_links")
    movie: "Movie" = Relationship(back_populates="actor_links")
