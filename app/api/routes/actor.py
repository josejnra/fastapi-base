from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import QueryableAttribute, selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db_session
from app.models import Actor, ActorMovie
from app.schemas import ActorResponse

router = APIRouter()


@router.post("/", response_model=Actor, status_code=status.HTTP_201_CREATED)
async def create_actor(actor: Actor, session: AsyncSession = Depends(get_db_session)):
    session.add(actor)
    await session.commit()
    await session.refresh(actor)
    return actor


@router.get("/", response_model=list[ActorResponse], status_code=status.HTTP_200_OK)
async def get_actors(session: AsyncSession = Depends(get_db_session)):
    result = await session.exec(select(Actor))
    actors = result.all()
    return actors


@router.get("/{actor_id}", response_model=ActorResponse, status_code=status.HTTP_200_OK)
async def get_actor(actor_id: int, session: AsyncSession = Depends(get_db_session)):
    statement = (
        select(Actor)
        .where(Actor.id == actor_id)
        .options(
            selectinload(cast(QueryableAttribute, Actor.addresses)),
            selectinload(cast(QueryableAttribute, Actor.movie_links)).selectinload(
                cast(QueryableAttribute, ActorMovie.movie)
            ),  # loads all movies associated with the actor
        )
    )
    result = await session.exec(statement)
    actor = result.first()

    if actor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Actor not found"
        )

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
