from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.database import SessionDep
from app.core.security import (
    CurrentActiveUserDep,
    authenticate_user,
    create_access_token,
)
from app.schemas import Token

router = APIRouter()


@router.post("/token", status_code=status.HTTP_200_OK, response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
):
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")


@router.post("/refresh", status_code=status.HTTP_200_OK, response_model=Token)
async def refresh_token(user: CurrentActiveUserDep):
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", status_code=status.HTTP_200_OK)
async def auth(
    current_user: CurrentActiveUserDep,
):
    return {"message": f"User {current_user.username} authenticated"}
