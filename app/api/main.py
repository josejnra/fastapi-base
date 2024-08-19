from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session, init_db
from app.models import (  # noqa: F401  # needed for sqlmodel in order to create tables
    Actor,
    ActorMovie,
    Address,
    Movie,
)
from app.schemas import ActorResponse, AddressResponse, MovieResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, None]:  # noqa: ARG001
    """Run tasks before and after the server starts.

    Args:
        app (FastAPI): implicit FastAPI application

    Returns:
        AsyncGenerator[Any, None]: application
    """
    await init_db()

    yield


def create_app() -> FastAPI:
    """Create FastAPI application.

    Returns:
        FastAPI: FastAPI application
    """
    app = FastAPI(
        title="Base code for FastAPI projects",
        description="My FastAPI description",
        openapi_url="/docs/openapi.json",
        docs_url="/docs",  # interactive API documentation
        redoc_url="/redoc",  # alternative automatic interactive API documentation
        root_path=get_settings().API_ROOT_PATH,
        lifespan=lifespan,
    )

    return app


app = create_app()


@app.get("/healthchecker")
def root():
    return {"message": "The API is LIVE!!"}


@app.get("/")
async def read_root():
    return {"Hello": "World"}
    # return RedirectResponse(url="/docs")


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


@app.post("/actors", response_model=Actor, status_code=status.HTTP_201_CREATED)
async def create_actor(actor: Actor, session: AsyncSession = Depends(get_db_session)):
    session.add(actor)
    await session.commit()
    await session.refresh(actor)
    return actor


@app.get("/actors", response_model=list[ActorResponse])
async def get_actors(session: AsyncSession = Depends(get_db_session)):
    result = await session.exec(select(Actor))
    actors = result.all()
    return actors


@app.get("/actors/{actor_id}", response_model=ActorResponse)
async def get_actor(actor_id: int, session: AsyncSession = Depends(get_db_session)):
    statement = (
        select(Actor)
        .where(Actor.id == actor_id)
        .options(
            selectinload(Actor.addresses),
            selectinload(Actor.movie_links).selectinload(
                ActorMovie.movie
            ),  # loads all movies associated with the actor
        )
    )
    result = await session.execute(statement)
    actor = result.scalar_one_or_none()

    if actor is None:
        raise HTTPException(status_code=404, detail="Actor not found")

    # turn ActorMovie list into an movie list
    movies = [link.movie for link in actor.movie_links]

    # building response model
    actor_response = ActorResponse(
        id=actor.id,
        name=actor.name,
        age=actor.age,
        created_at=actor.created_at,
        updated_at=actor.updated_at,
        addresses=actor.addresses,
        movies=movies,
    )

    return actor_response


@app.get("/addresses", response_model=list[AddressResponse])
async def get_addresses(session: AsyncSession = Depends(get_db_session)):
    result = await session.exec(select(Address))
    address = result.all()
    return address


@app.get("/addresses/{address_id}", response_model=AddressResponse)
async def get_address(address_id: int, session: AsyncSession = Depends(get_db_session)):
    address = await session.get(Address, address_id)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Address not found"
        )
    return address


@app.get("/movies", response_model=list[MovieResponse])
async def get_movies(session: AsyncSession = Depends(get_db_session)):
    result = await session.exec(select(Movie))
    movies = result.all()
    return movies


@app.get("/movies/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id: int, session: AsyncSession = Depends(get_db_session)):
    statement = (
        select(Movie)
        .where(Movie.id == movie_id)
        .options(
            selectinload(Movie.actor_links).selectinload(
                ActorMovie.actor
            ),  # loads all actors associated with the movie
        )
    )
    result = await session.execute(statement)
    movie = result.scalar_one_or_none()

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
