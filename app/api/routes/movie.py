from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import QueryableAttribute, selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db_session
from app.models import Actor, ActorMovie, Movie
from app.schemas import MovieParam, MovieResponse, MovieResponseDetailed

router = APIRouter()


@router.post(
    "/", response_model=MovieResponseDetailed, status_code=status.HTTP_201_CREATED
)
async def create_movie(
    movie: MovieParam,
    session: AsyncSession = Depends(get_db_session),
):
    # search for actors
    actors: list[Actor] = []
    for actor_id in movie.actors:
        actor = await session.get(Actor, actor_id)
        if actor is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Actor {actor_id} not found",
            )
        actors.append(actor)

    # create movie
    new_movie = Movie(**movie.model_dump())

    session.add(new_movie)

    # create actor-movie links
    actor_movies = [ActorMovie(actor=actor, movie=new_movie) for actor in actors]

    session.add_all(actor_movies)
    await session.commit()

    return MovieResponseDetailed(actors=actors, **new_movie.model_dump())


@router.get("/", response_model=MovieResponse, status_code=status.HTTP_200_OK)
async def get_movies(
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    count_statement = select(func.count()).select_from(Movie)
    result_count = await session.exec(count_statement)

    statement = select(Movie).offset((page - 1) * page_size).limit(page_size)
    result = await session.exec(statement)

    movies = MovieResponse(
        movies=[MovieResponseDetailed(**movie.model_dump()) for movie in result.all()],
        total=result_count.one(),
        page=page,
        page_size=page_size,
    )
    return movies


@router.get(
    "/{movie_id}", response_model=MovieResponseDetailed, status_code=status.HTTP_200_OK
)
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found"
        )

    # turn ActorMovie list into an actor list
    actors = [link.actor for link in movie.actor_links]

    # building response model
    movie_response = MovieResponseDetailed(
        id=movie.id,
        title=movie.title,
        year=movie.year,
        rating=movie.rating,
        created_at=movie.created_at,
        updated_at=movie.updated_at,
        actors=actors,
    )

    return movie_response
