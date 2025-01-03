from typing import cast

from fastapi import APIRouter, HTTPException, Query, status
from opentelemetry import trace
from sqlalchemy.orm import QueryableAttribute, selectinload
from sqlmodel import func, select

from app.core.database import SessionDep
from app.core.logger import logger
from app.core.security import CurrentActiveUserDep
from app.core.telemetry import meter, tracer
from app.models import Actor, ActorMovie
from app.schemas import ActorParam, ActorResponse, ActorResponseDetailed

router = APIRouter()


# catch an error and log it
@logger.catch
@router.post(
    "/",
    response_model=ActorResponseDetailed,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "model": ActorResponseDetailed,
            "description": "Actor created",
        }
    },
)
async def create_actor(
    actor: ActorParam,
    session: SessionDep,
):
    work_counter = meter.create_counter(
        name="actor_creation_counter",
        unit="1",
        description="Counts the number of calls to actors endpoint",
    )
    work_counter.add(1)

    with tracer.start_as_current_span("parsing-actor") as span:
        span.set_attribute("actor", actor.name)
        child = logger.bind(**actor.model_dump())
        child.debug("Creating actor")
        new_actor = Actor(**actor.model_dump())

    with tracer.start_as_current_span("staging-actor") as span:
        session.add(new_actor)
    with tracer.start_as_current_span("commiting-actor") as span:
        await session.commit()
        span.set_status(trace.Status(trace.StatusCode.OK))

    with tracer.start_as_current_span("refreshing-actor") as span:
        await session.refresh(new_actor)
        span.set_status(trace.Status(trace.StatusCode.OK))
    return ActorResponseDetailed(**new_actor.model_dump())


@logger.catch
@router.get("/", response_model=ActorResponse, status_code=status.HTTP_200_OK)
async def get_actors(
    session: SessionDep,
    _: CurrentActiveUserDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    with tracer.start_as_current_span("count-actors") as span:
        count_statement = select(func.count()).select_from(Actor)
        result_count = await session.exec(count_statement)
        count = result_count.one()
        span.set_attribute("actor-count", count)
        span.set_status(trace.Status(trace.StatusCode.OK))

    with tracer.start_as_current_span("get-actors") as span:
        statement = select(Actor).offset((page - 1) * page_size).limit(page_size)
        result = await session.exec(statement)
        span.set_status(trace.Status(trace.StatusCode.OK))

    with tracer.start_as_current_span("parse-actors") as span:
        actors = ActorResponse(
            actors=[
                ActorResponseDetailed(**actor.model_dump()) for actor in result.all()
            ],
            total=count,
            page=page,
            page_size=page_size,
        )
        return actors


@logger.catch
@router.get(
    "/{actor_id}",
    response_model=ActorResponseDetailed,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_201_CREATED: {
            "model": ActorResponseDetailed,
            "description": "Retrieve specific actor",
        },
    },
)
async def get_actor(actor_id: int, session: SessionDep):
    child = logger.bind(actor_id=actor_id)
    child.debug("Getting actor")

    with tracer.start_as_current_span("get-actor") as span:
        span.set_attribute("actor-id", actor_id)
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
        span.set_status(trace.Status(trace.StatusCode.OK))

    if actor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Actor not found"
        )

    # turn ActorMovie list into an movie list
    movies = [link.movie for link in actor.movie_links]

    with tracer.start_as_current_span("parsing-actor") as span:
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
