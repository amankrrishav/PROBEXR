from typing import Annotated, Optional
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select

from app.config import get_config
from app.db import get_session
from app.models.user import User

# Load config
cfg = get_config()

SECRET_KEY = cfg.SECRET_KEY
ALGORITHM = cfg.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# Argon2 hasher (modern, secure)
ph = PasswordHasher()


# -------------------------
# Password Handling
# -------------------------

def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        ph.verify(hashed, plain)
        return True
    except VerifyMismatchError:
        return False


# -------------------------
# JWT Token Creation
# -------------------------

from typing import Any

def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -------------------------
# DB Utility
# -------------------------

def get_user_by_email(session: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise _credentials_exception()

    if "sub" not in payload:
        raise _credentials_exception()
    return payload


async def get_current_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    session: Session = Depends(get_session),
) -> User:
    """
    Strict auth dependency: requires a valid Bearer token and existing user.
    """
    if not token:
        raise _credentials_exception()

    payload = _decode_token(token)
    email = payload.get("sub")
    if not email or not isinstance(email, str):
        raise _credentials_exception()
    
    user = get_user_by_email(session, email)
    if not user:
        raise _credentials_exception()
    return user


async def get_optional_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    session: Session = Depends(get_session),
) -> Optional[User]:
    """
    Optional auth: returns a user when token is valid, otherwise None.
    Suitable for routes that are public but can tailor responses for logged-in users.
    """
    if not token:
        return None

    try:
        payload = _decode_token(token)
    except HTTPException:
        # Invalid token -> treat as anonymous
        return None

    email = payload.get("sub")
    if not email:
        return None

    return get_user_by_email(session, email)