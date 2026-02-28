from typing import Annotated, Any, Optional
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status, Request, Response
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



def get_token_from_request(request: Request) -> Optional[str]:
    token = request.cookies.get("access_token")
    if token and token.startswith("Bearer "):
        return token.split(" ")[1]
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    
    return None

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

def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def set_auth_cookie(response: Response, token: str) -> None:
    is_secure = cfg.environment == "production"
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        samesite="lax",
        secure=is_secure,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )



# -------------------------
# DB Utility
# -------------------------

def get_user_by_email(session: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

def register_user(session: Session, email: str, password: str) -> User:
    existing = get_user_by_email(session, email)
    if existing:
        raise ValueError("Email already registered")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        signup_source="app",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def authenticate_user(session: Session, email: str, password: str) -> User:
    user = get_user_by_email(session, email)
    if user is None or not verify_password(password, user.hashed_password):
        raise ValueError("Invalid credentials")

    user.last_login_at = datetime.now(timezone.utc)
    session.add(user)
    session.commit()
    return user

def upgrade_user_to_pro(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if not user:
        raise ValueError("User not found")

    if user.plan != "pro":
        user.plan = "pro"
        session.add(user)
        session.commit()
        session.refresh(user)

    return user

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
    token: Annotated[Optional[str], Depends(get_token_from_request)],
    session: Session = Depends(get_session),
) -> User:
    """
    Strict auth dependency: requires a valid Bearer token and existing active user.
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
    if not user.is_active:
        raise _credentials_exception()
    return user


async def get_optional_user(
    token: Annotated[Optional[str], Depends(get_token_from_request)],
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

    user = get_user_by_email(session, email)
    if user and not user.is_active:
        return None
    return user