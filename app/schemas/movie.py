from datetime import datetime

from app.models import Actor, MovieBase


class MovieResponse(MovieBase):
    id: int
    title: str
    year: int
    rating: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    actors: list[Actor] = []
