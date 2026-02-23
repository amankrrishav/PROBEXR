from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db import get_session
from app.deps import CurrentUser
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
    hash_password,
    verify_password,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, session: Session = Depends(get_session)) -> Token:
    existing = get_user_by_email(session, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token({"sub": user.email})
    return Token(access_token=token)


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> Token:
    user = get_user_by_email(session, payload.email)

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": user.email})
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
def read_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)

