from typing import cast

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import QueryableAttribute, selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db_session
from app.models import (
    ActorMovie,
    Movie,
)
from app.schemas import MovieResponse

router = APIRouter()


@router.get("/", response_model=list[MovieResponse])
async def get_movies(session: AsyncSession = Depends(get_db_session)):
    result = await session.exec(select(Movie))
    movies = result.all()
    return movies


@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id: int, session: AsyncSession = Depends(get_db_session)):
    statement = (
        select(Movie)
        .where(Movie.id == movie_id)
        .options(
            selectinload(cast(QueryableAttribute, Movie.actor_links)).selectinload(
                cast(QueryableAttribute, ActorMovie.actor)
            ),  # loads all actors associated with the movie
        )
    )
    result = await session.exec(statement)
    movie = result.first()

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    # turn ActorMovie list into an actor list
    actors = [link.actor for link in movie.actor_links]

    # building response model
    movie_response = MovieResponse(
        id=movie.id,
        title=movie.title,
        year=movie.year,
        rating=movie.rating,
        created_at=movie.created_at,
        updated_at=movie.updated_at,
        actors=actors,
    )

    return movie_response
