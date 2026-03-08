from typing import Annotated, Any, Optional
from datetime import datetime, timedelta, timezone
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status, Request, Response
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import get_config
from app.db import get_session
from app.models.user import User
from app.models.refresh_token import RefreshToken

# Load config
cfg = get_config()

SECRET_KEY = cfg.SECRET_KEY
ALGORITHM = cfg.ALGORITHM


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
# JWT Access Token
# -------------------------

def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=cfg.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def set_auth_cookie(response: Response, token: str) -> None:
    is_prod = cfg.environment == "production"
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        samesite="none" if is_prod else "lax",
        secure=is_prod,  # Mandatory for samesite=none
        max_age=cfg.access_token_expire_minutes * 60,
    )


# -------------------------
# Refresh Token
# -------------------------

async def create_refresh_token(session: AsyncSession, user_id: int) -> RefreshToken:
    """Create a new refresh token with a fresh family (new login session)."""
    token = RefreshToken(
        token=str(uuid.uuid4()),
        user_id=user_id,
        token_family=str(uuid.uuid4()),
        expires_at=(datetime.utcnow() + timedelta(days=cfg.refresh_token_expire_days)).replace(tzinfo=None),
    )
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return token


async def rotate_refresh_token(session: AsyncSession, old_token_str: str) -> tuple[RefreshToken, User]:
    """
    Rotate a refresh token: revoke the old one and issue a new one in the same family.

    If the old token is already revoked (reuse detected), revoke the ENTIRE family
    as a security measure — the token may have been stolen.

    Returns (new_token, user) on success.
    Raises HTTPException on any failure.
    """
    statement = select(RefreshToken).where(RefreshToken.token == old_token_str)
    result = await session.execute(statement)
    old_token = result.scalars().first()

    if not old_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Reuse detection: if token is already revoked, someone is replaying it
    if old_token.is_revoked:
        await _revoke_family(session, old_token.token_family)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected — all sessions revoked",
        )

    # Compare expiry — handle both naive (SQLite) and aware (PostgreSQL) datetimes
    now_utc = datetime.utcnow()
    expires = old_token.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now_utc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    # Look up the user
    user_stmt = select(User).where(User.id == old_token.user_id)
    user_result = await session.execute(user_stmt)
    user = user_result.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Revoke old token
    old_token.is_revoked = True
    session.add(old_token)

    # Issue new token in the same family
    new_token = RefreshToken(
        token=str(uuid.uuid4()),
        user_id=old_token.user_id,
        token_family=old_token.token_family,
        expires_at=(datetime.utcnow() + timedelta(days=cfg.refresh_token_expire_days)).replace(tzinfo=None),
    )
    session.add(new_token)
    await session.commit()
    await session.refresh(new_token)

    return new_token, user


async def revoke_refresh_token(session: AsyncSession, token_str: str) -> None:
    """Revoke a single refresh token (e.g. on logout)."""
    statement = select(RefreshToken).where(RefreshToken.token == token_str)
    result = await session.execute(statement)
    token = result.scalars().first()
    if token:
        token.is_revoked = True
        session.add(token)
        await session.commit()


async def revoke_all_user_tokens(session: AsyncSession, user_id: int) -> int:
    """Revoke all refresh tokens for a user. Returns the count revoked."""
    statement = select(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False,  # noqa: E712
    )
    result = await session.execute(statement)
    tokens = result.scalars().all()
    count = 0
    for token in tokens:
        token.is_revoked = True
        session.add(token)
        count += 1
    await session.commit()
    return count


async def _revoke_family(session: AsyncSession, token_family: str) -> None:
    """Revoke all tokens in a family (reuse detection response)."""
    statement = select(RefreshToken).where(
        RefreshToken.token_family == token_family,
        RefreshToken.is_revoked == False,  # noqa: E712
    )
    result = await session.execute(statement)
    tokens = result.scalars().all()
    for token in tokens:
        token.is_revoked = True
        session.add(token)
    await session.commit()


def set_refresh_cookie(response: Response, token_str: str) -> None:
    is_prod = cfg.environment == "production"
    response.set_cookie(
        key="refresh_token",
        value=token_str,
        httponly=True,
        samesite="none" if is_prod else "lax",
        secure=is_prod,  # Mandatory for samesite=none
        path="/auth",  # Only sent to auth endpoints
        max_age=cfg.refresh_token_expire_days * 24 * 60 * 60,
    )


def delete_auth_cookies(response: Response) -> None:
    """Clear both access and refresh token cookies."""
    response.delete_cookie("access_token", httponly=True, samesite="lax")
    response.delete_cookie("refresh_token", httponly=True, samesite="lax", path="/auth")


# -------------------------
# DB Utility
# -------------------------

async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    return result.scalars().first()

async def register_user(session: AsyncSession, email: str, password: str) -> User:
    existing = await get_user_by_email(session, email)
    if existing:
        raise ValueError("Email already registered")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        signup_source="app",
        created_at=datetime.utcnow(),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(session, email)
    if user is None or not verify_password(password, user.hashed_password):
        raise ValueError("Invalid credentials")

    user.last_login_at = datetime.utcnow()
    session.add(user)
    await session.commit()
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
    session: AsyncSession = Depends(get_session),
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
    
    user = await get_user_by_email(session, email)
    if not user:
        raise _credentials_exception()
    if not user.is_active:
        raise _credentials_exception()
    return user


async def get_optional_user(
    token: Annotated[Optional[str], Depends(get_token_from_request)],
    session: AsyncSession = Depends(get_session),
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

    user = await get_user_by_email(session, email)
    if user and not user.is_active:
        return None
    return user