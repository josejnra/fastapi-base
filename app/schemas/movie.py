from datetime import datetime

from pydantic import BaseModel, Field

from app.models import Actor, MovieBase


class MovieParam(BaseModel):
    title: str = Field(
        title="movie title",
        description="Title of the movie",
        examples=["The Godfather"],
        min_length=1,
        max_length=255,
    )
    year: int = Field(
        title="release year",
        description="Year of the movie",
        examples=[1972],
        ge=1900,
        le=2200,
    )
    rating: int | None = Field(
        default=0,
        title="rating",
        description="Rating of the movie",
        examples=[],
        ge=0,
        le=5,
    )

    actors: list[int] = Field(
        default=[],
        title="movie cast",
        description="List of actor ids",
        examples=[[1, 2, 3]],
    )


class MovieResponseDetailed(MovieBase):
    id: int
    title: str
    year: int
    rating: int
    created_at: datetime
    updated_at: datetime | None = None

    actors: list[Actor] = []


class MovieResponse(BaseModel):
    total: int
    page: int
    page_size: int
    movies: list[MovieResponseDetailed] = []
