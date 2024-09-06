from datetime import datetime

from pydantic import BaseModel, Field, SecretStr

from app.models import UserBase


class UserParam(BaseModel):
    name: str = Field(
        title="name",
        description="Name of the user",
        examples=["Brad Pitt"],
        min_length=1,
        max_length=255,
    )
    username: str = Field(
        title="username",
        description="Username of the user",
        examples=["bradpitt"],
        min_length=1,
        max_length=255,
    )
    email: str = Field(
        title="email",
        description="Email of the user",
        examples=["brad.pitt@gmail.com"],
        min_length=1,
        max_length=255,
    )
    password: SecretStr = Field(
        title="password",
        description="Password of the user",
        examples=["123456"],
        min_length=1,
        max_length=255,
    )


class UserResponseDetailed(UserBase):
    id: int
    disabled: bool
    created_at: datetime
    updated_at: datetime | None = None


class UserResponse(BaseModel):
    total: int
    page: int
    page_size: int
