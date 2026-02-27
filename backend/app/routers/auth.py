from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlmodel import Session

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
    upgrade_user_to_pro,
    set_auth_cookie,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest, 
    response: Response,
    session: DbSession
) -> Token:
    try:
        user = register_user(session, payload.email, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    token = create_access_token({"sub": user.email})
    set_auth_cookie(response, token)
    return Token(access_token=token)


@router.post("/login", response_model=Token)
def login(
    payload: LoginRequest, 
    response: Response,
    session: DbSession
) -> Token:
    try:
        user = authenticate_user(session, payload.email, payload.password)
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
def read_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post("/upgrade/demo-pro", response_model=UserRead)
def upgrade_demo_pro(
    current_user: CurrentUser, 
    session: DbSession
) -> UserRead:
    """
    Demo-only endpoint to flip the current user to Pro plan.
    No real billing, safe for testing subscription flows.
    """
    try:
        assert current_user.id is not None
        user = upgrade_user_to_pro(session, current_user.id)
        return UserRead.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

