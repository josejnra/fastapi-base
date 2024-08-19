from datetime import datetime

from app.models import Actor
from app.models.address import AddressBase


class AddressResponse(AddressBase):
    id: int | None = None
    actor: Actor | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
