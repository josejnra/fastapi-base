from datetime import datetime

from pydantic import BaseModel, Field

from app.models import ActorBase, Address, Movie


class ActorParam(BaseModel):
    name: str = Field(
        title="name", description="Name of the actor", examples=["Brad Pitt"]
    )
    age: int = Field(title="age", description="Age of the actor", examples=[42])


class ActorResponseDetailed(ActorBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    addresses: list[Address] = []
    movies: list[Movie] = []


class ActorResponse(BaseModel):
    total: int
    page: int
    page_size: int
    actors: list[ActorResponseDetailed] = []
