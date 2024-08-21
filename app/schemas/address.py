from datetime import datetime

from pydantic import BaseModel, Field

from app.models import Actor
from app.models.address import AddressBase


class AddressParam(BaseModel):
    country: str = Field(
        title="country",
        description="Country of the address",
        examples=["Brazil"],
    )
    city: str = Field(
        title="city",
        description="City of the address",
        examples=["São Paulo"],
    )
    address_line_1: str = Field(
        title="address line 1",
        description="Address line 1 of the address",
        examples=["Rua do Rio"],
    )
    address_line_2: str | None = Field(
        default=None,
        title="address line 2",
        description="Address line 2 of the address",
        examples=["Bairro do Rio"],
    )
    post_code: str = Field(
        title="postal code",
        description="Postal code of the address",
        examples=["01310-000"],
    )
    actor_id: int = Field(title="actor id", description="Actor id", examples=[1])


class AddressResponseDetailed(AddressBase):
    id: int
    actor: Actor | None = None
    created_at: datetime
    updated_at: datetime | None = None


class AddressResponse(BaseModel):
    total: int
    page: int
    page_size: int
    addresses: list[AddressResponseDetailed]
