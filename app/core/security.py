from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
)
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlmodel import select

from app.core.config import get_settings
from app.core.database import SessionDep
from app.models import User
from app.schemas import TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{get_settings().API_ROOT_PATH}/auth/token"
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def get_user(session: SessionDep, username: str) -> User:
    statement = select(User).where(User.username == username)
    result = await session.exec(statement)
    user = result.first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


async def authenticate_user(session: SessionDep, username: str, password: str):
    user = await get_user(session, username)
    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User or password incorrect"
        )
    return user


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, get_settings().SECRET_KEY, algorithm=get_settings().ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = await get_user(session, username=token_data.username)
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user
