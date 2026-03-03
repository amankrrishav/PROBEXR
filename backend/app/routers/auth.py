from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
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
    create_refresh_token,
    rotate_refresh_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
    get_user_by_email,
    register_user,
    authenticate_user,
    set_auth_cookie,
    set_refresh_cookie,
    delete_auth_cookies,
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

    access_token = create_access_token({"sub": user.email})
    refresh = await create_refresh_token(session, user.id)

    set_auth_cookie(response, access_token)
    set_refresh_cookie(response, refresh.token)
    return Token(access_token=access_token, refresh_token=refresh.token)


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

    access_token = create_access_token({"sub": user.email})
    refresh = await create_refresh_token(session, user.id)

    set_auth_cookie(response, access_token)
    set_refresh_cookie(response, refresh.token)
    return Token(access_token=access_token, refresh_token=refresh.token)


@router.post("/refresh", response_model=Token)
async def refresh(
    request: Request,
    response: Response,
    session: DbSession,
) -> Token:
    """Rotate refresh token and issue new access + refresh tokens."""
    old_refresh = request.cookies.get("refresh_token")
    if not old_refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )

    new_refresh, user = await rotate_refresh_token(session, old_refresh)
    access_token = create_access_token({"sub": user.email})

    set_auth_cookie(response, access_token)
    set_refresh_cookie(response, new_refresh.token)
    return Token(access_token=access_token, refresh_token=new_refresh.token)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    session: DbSession,
) -> dict:
    # Revoke the refresh token in DB if present
    old_refresh = request.cookies.get("refresh_token")
    if old_refresh:
        await revoke_refresh_token(session, old_refresh)

    delete_auth_cookies(response)
    return {"message": "Logged out"}


@router.post("/logout-all")
async def logout_all(
    current_user: CurrentUser,
    response: Response,
    session: DbSession,
) -> dict:
    """Revoke all refresh tokens for the current user (log out everywhere)."""
    count = await revoke_all_user_tokens(session, current_user.id)
    delete_auth_cookies(response)
    return {"message": f"Logged out of all sessions ({count} tokens revoked)"}


@router.get("/me", response_model=UserRead)
async def read_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
