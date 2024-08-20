from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import QueryableAttribute, selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db_session
from app.models import Actor, ActorMovie
from app.schemas import ActorParam, ActorResponse, ActorResponseDetailed

router = APIRouter()


@router.post(
    "/", response_model=ActorResponseDetailed, status_code=status.HTTP_201_CREATED
)
async def create_actor(
    actor: ActorParam,
    session: AsyncSession = Depends(get_db_session),
):
    new_actor = Actor(**actor.model_dump())

    session.add(new_actor)
    await session.commit()
    await session.refresh(new_actor)
    return ActorResponseDetailed(**new_actor.model_dump())


@router.get("/", response_model=ActorResponse, status_code=status.HTTP_200_OK)
async def get_actors(
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    count_statement = select(func.count()).select_from(Actor)
    result_count = await session.exec(count_statement)

    statement = select(Actor).offset((page - 1) * page_size).limit(page_size)
    result = await session.exec(statement)

    actors = ActorResponse(
        actors=[ActorResponseDetailed(**actor.model_dump()) for actor in result.all()],
        total=result_count.one(),
        page=page,
        page_size=page_size,
    )
    return actors


@router.get(
    "/{actor_id}", response_model=ActorResponseDetailed, status_code=status.HTTP_200_OK
)
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
    actor_response = ActorResponseDetailed(
        id=actor.id,
        name=actor.name,
        age=actor.age,
        created_at=actor.created_at,
        updated_at=actor.updated_at,
        addresses=actor.addresses,
        movies=movies,
    )

    return actor_response
