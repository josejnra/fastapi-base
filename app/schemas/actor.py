from datetime import datetime

from app.models import ActorBase, Address, Movie


class ActorResponse(ActorBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    addresses: list[Address] = []
    movies: list[Movie] = []
