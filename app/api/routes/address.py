from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db_session
from app.models import (
    Address,
)
from app.schemas import AddressResponse

router = APIRouter()


@router.get("/", response_model=list[AddressResponse])
async def get_addresses(session: AsyncSession = Depends(get_db_session)):
    result = await session.exec(select(Address))
    address = result.all()
    return address


@router.get("/{address_id}", response_model=AddressResponse)
async def get_address(address_id: int, session: AsyncSession = Depends(get_db_session)):
    address = await session.get(Address, address_id)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Address not found"
        )
    return address
