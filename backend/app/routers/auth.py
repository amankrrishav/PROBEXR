from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import CurrentUser, DbSession
from app.models.user import User
from app.schemas import (
    LoginRequest,
    RegisterRequest,
    Token,
    UserRead,
)
from app.services.auth import (
    create_access_token,
    get_user_by_email,
    register_user,
    authenticate_user,
    set_auth_cookie,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest, 
    response: Response,
    session: DbSession
) -> Token:
    try:
        user = await register_user(session, payload.email, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    token = create_access_token({"sub": user.email})
    set_auth_cookie(response, token)
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(
    payload: LoginRequest, 
    response: Response,
    session: DbSession
) -> Token:
    try:
        user = await authenticate_user(session, payload.email, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    token = create_access_token({"sub": user.email})
    set_auth_cookie(response, token)
    return Token(access_token=token)


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie("access_token", httponly=True, samesite="lax")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserRead)
async def read_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


