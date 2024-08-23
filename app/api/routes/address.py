from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db_session
from app.core.logger import logger
from app.models import Actor, Address
from app.schemas import AddressParam, AddressResponse, AddressResponseDetailed

router = APIRouter()


@logger.catch
@router.post(
    "/", response_model=AddressResponseDetailed, status_code=status.HTTP_201_CREATED
)
async def create_address(
    address: AddressParam,
    session: AsyncSession = Depends(get_db_session),
):
    child = logger.bind(**address.model_dump())
    child.debug("Creating address")

    actor = await session.get(Actor, address.actor_id)
    if not actor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Actor not found"
        )

    new_address = Address(actor=actor, **address.model_dump())
    session.add(new_address)
    await session.commit()
    await session.refresh(new_address)

    return AddressResponseDetailed(actor=new_address.actor, **new_address.model_dump())


@logger.catch
@router.get("/", response_model=AddressResponse, status_code=status.HTTP_200_OK)
async def get_addresses(
    session: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    count_statement = select(func.count()).select_from(Address)
    result_count = await session.exec(count_statement)

    statement = select(Address).offset((page - 1) * page_size).limit(page_size)
    result = await session.exec(statement)

    addresses = AddressResponse(
        total=result_count.one(),
        page=page,
        page_size=page_size,
        addresses=[
            AddressResponseDetailed(**address.model_dump()) for address in result.all()
        ],
    )
    return addresses


@logger.catch
@router.get(
    "/{address_id}",
    response_model=AddressResponseDetailed,
    status_code=status.HTTP_200_OK,
)
async def get_address(address_id: int, session: AsyncSession = Depends(get_db_session)):
    address = await session.get(Address, address_id)
    child = logger.bind(address_id=address_id)
    child.debug("Getting address")

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Address not found"
        )
    return address
