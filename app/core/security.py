from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
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

TokenDep = Annotated[str, Depends(oauth2_scheme)]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against its hashed version.

    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hashes a plain password using the configured password context.

    Args:
        password (str): The plain text password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


async def get_user(session: SessionDep, username: str) -> User:
    """
    Retrieves a user from the database by username.

    Args:
        session (SessionDep): The database session dependency.
        username (str): The username to search for.

    Raises:
        HTTPException: If the user is not found.

    Returns:
        User: The user object if found.
    """
    statement = select(User).where(User.username == username)
    result = await session.exec(statement)
    user = result.first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


async def authenticate_user(session: SessionDep, username: str, password: str) -> User:
    """
    Authenticates a user by verifying their username and password.

    Args:
        session (SessionDep): The database session dependency.
        username (str): The username to authenticate.
        password (str): The plain text password to verify.

    Raises:
        HTTPException: If the username or password is incorrect.

    Returns:
        User: The authenticated user object.
    """
    user = await get_user(session, username)
    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User or password incorrect"
        )
    return user


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """
    Creates a JWT access token with an expiration.

    Args:
        data (dict[str, Any]): The data to encode in the token.
        expires_delta (timedelta | None, optional): The token expiration delta. Defaults to None.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, get_settings().SECRET_KEY, algorithm=get_settings().ALGORITHM
    )
    return encoded_jwt


async def get_current_user(session: SessionDep, token: TokenDep) -> User:
    """
    Retrieves the current user based on the provided JWT token.

    Args:
        session (SessionDep): The database session dependency.
        token (str): The JWT token from the request.

    Raises:
        HTTPException: If the credentials are invalid or the user does not exist.

    Returns:
        User: The current authenticated user.
    """
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


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(
    current_user: CurrentUserDep,
) -> User:
    """
    Ensures the current user is active (not disabled).

    Args:
        current_user (User): The current authenticated user.

    Raises:
        HTTPException: If the user is inactive.

    Returns:
        User: The current active user.
    """
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


CurrentActiveUserDep = Annotated[User, Depends(get_current_active_user)]
