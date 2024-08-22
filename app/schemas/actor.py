from datetime import datetime

from pydantic import BaseModel, Field

from app.models import ActorBase, Address, Movie


class ActorParam(BaseModel):
    name: str = Field(
        title="name",
        description="Name of the actor",
        examples=["Brad Pitt"],
        min_length=1,
        max_length=255,
    )
    age: int = Field(
        title="age", description="Age of the actor", examples=[42], ge=0, le=130
    )


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
