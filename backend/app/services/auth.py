from typing import Annotated, Any, Optional
from datetime import datetime, timedelta, timezone
import hashlib
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status, Request, Response
import jwt
from jwt.exceptions import PyJWTError
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import get_config
from app.db import get_session
from app.models.user import User
from app.models.refresh_token import RefreshToken

# ALGORITHM is read once at import time — it is a static deployment parameter
# that never changes at runtime, so this is safe.
ALGORITHM = get_config().ALGORITHM


class DuplicateEmailError(ValueError):
    """Raised by register_user when the email is already registered.

    Callers should catch this specific exception rather than the broad
    ValueError so future code paths can handle duplicates cleanly without
    accidentally catching unrelated ValueErrors.
    """
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email already registered: {email}")


def create_email_verification_token(email: str) -> str:
    """Create a short-lived token for email verification."""
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "email_verification",
    }
    return jwt.encode(to_encode, get_config().signing_key, algorithm=ALGORITHM)


async def verify_email_token(session: AsyncSession, token: str) -> User:
    """Verify the email verification token and mark the user as verified."""
    try:
        payload = jwt.decode(token, get_config().verification_key, algorithms=[ALGORITHM])
        if payload.get("type") != "email_verification":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification link is invalid or has expired",
        )

    user = await get_user_by_email(session, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


def create_password_reset_token(email: str) -> str:
    """Create a short-lived token for password reset."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "password_reset",
    }
    return jwt.encode(to_encode, get_config().signing_key, algorithm=ALGORITHM)


async def verify_password_reset_token(session: AsyncSession, token: str, new_password: str) -> User:
    """Verify a password reset token and update the user's password."""
    try:
        payload = jwt.decode(token, get_config().verification_key, algorithms=[ALGORITHM])
        if payload.get("type") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reset link is invalid or has expired",
        )

    user = await get_user_by_email(session, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    user.hashed_password = hash_password(new_password)
    session.add(user)

    # Revoke all refresh tokens so all existing sessions are invalidated
    await revoke_all_user_tokens(session, user.id)

    await session.commit()
    await session.refresh(user)
    return user


def create_magic_link_token(email: str) -> str:
    """
    Create a short-lived token for magic link authentication.
    Includes a `jti` (JWT ID) claim for one-time use enforcement.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "magic_link",
        "jti": str(uuid.uuid4()),  # Unique token ID — stored on first use
    }
    return jwt.encode(to_encode, get_config().signing_key, algorithm=ALGORITHM)


async def _mark_token_used(
    session: AsyncSession,
    jti: str,
    token_type: str,
    expires_at: datetime,
) -> None:
    """
    Insert the jti into used_token.  If the jti already exists
    (unique constraint violation) this raises an IntegrityError,
    which the caller converts into a 401.
    """
    from app.models.used_token import UsedToken
    from sqlalchemy.exc import IntegrityError

    record = UsedToken(
        jti=jti,
        token_type=token_type,
        expires_at=expires_at,
    )
    session.add(record)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This link has already been used. Please request a new one.",
        )


async def verify_magic_link_token(session: AsyncSession, token: str) -> User:
    """
    Verify a magic link token and return the user.
    Enforces one-time use via the UsedToken table.
    """
    try:
        payload = jwt.decode(token, get_config().verification_key, algorithms=[ALGORITHM])
        if payload.get("type") != "magic_link":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        jti = payload.get("jti")
        if not jti:
            # Legacy tokens without jti — fall back to hashing the full token
            jti = hashlib.sha256(token.encode()).hexdigest()
        exp_ts = payload.get("exp")
        expires_at = (
            datetime.fromtimestamp(exp_ts, tz=timezone.utc).replace(tzinfo=None)
            if exp_ts else datetime.now(timezone.utc).replace(tzinfo=None)
        )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Enforce one-time use — raises 401 if already consumed
    await _mark_token_used(session, jti, "magic_link", expires_at)

    user = await get_user_by_email(session, email)
    if not user:
        # Just-In-Time Provisioning for new magic link users
        user = await register_user(session, email, str(uuid.uuid4()))

    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    user.is_verified = True
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


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


def verify_password(plain: str, hashed: Optional[str]) -> bool:
    if not hashed:
        return False
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
    expire = datetime.now(timezone.utc) + timedelta(minutes=get_config().access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, get_config().signing_key, algorithm=ALGORITHM)


def set_auth_cookie(response: Response, token: str) -> None:
    is_prod = get_config().environment == "production"
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        samesite="none" if is_prod else "lax",
        secure=is_prod,  # Mandatory for samesite=none
        max_age=get_config().access_token_expire_minutes * 60,
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
        expires_at=(datetime.now(timezone.utc) + timedelta(days=get_config().refresh_token_expire_days)).replace(tzinfo=None),
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
    now_utc = datetime.now(timezone.utc)
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
        expires_at=(datetime.now(timezone.utc) + timedelta(days=get_config().refresh_token_expire_days)).replace(tzinfo=None),
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
    statement = (
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
        .values(is_revoked=True)
    )
    result = await session.execute(statement)
    await session.commit()
    return result.rowcount  # type: ignore[return-value]


async def _revoke_family(session: AsyncSession, token_family: str) -> None:
    """Revoke all tokens in a family (reuse detection response)."""
    statement = (
        update(RefreshToken)
        .where(
            RefreshToken.token_family == token_family,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
        .values(is_revoked=True)
    )
    await session.execute(statement)
    await session.commit()


def set_refresh_cookie(response: Response, token_str: str) -> None:
    is_prod = get_config().environment == "production"
    response.set_cookie(
        key="refresh_token",
        value=token_str,
        httponly=True,
        samesite="none" if is_prod else "lax",
        secure=is_prod,  # Mandatory for samesite=none
        path="/api/v1/auth",  # Matches actual router mount: /api/v1/auth/*
        max_age=get_config().refresh_token_expire_days * 24 * 60 * 60,
    )


def delete_auth_cookies(response: Response) -> None:
    """Clear both access and refresh token cookies.

    Must use the same samesite/secure attributes that were used when setting
    them, otherwise the browser will not remove them.
    """
    is_prod = get_config().environment == "production"
    samesite_value = "none" if is_prod else "lax"
    response.delete_cookie(
        "access_token", httponly=True, samesite=samesite_value, secure=is_prod
    )
    response.delete_cookie(
        "refresh_token", httponly=True, samesite=samesite_value, secure=is_prod, path="/api/v1/auth"
    )


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
        raise DuplicateEmailError(email)

    user = User(
        email=email,
        hashed_password=hash_password(password),
        signup_source="app",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    from app.lockout import get_lockout_manager
    mgr = get_lockout_manager()

    # Check lockout BEFORE hitting the DB — fail fast, don't leak timing info
    if await mgr.is_locked(email):
        raise ValueError(
            "Account temporarily locked due to too many failed login attempts. "
            "Please try again in 15 minutes or reset your password."
        )

    user = await get_user_by_email(session, email)
    if user is None or not verify_password(password, user.hashed_password or ""):
        # Record the failure regardless of whether the email exists.
        # This prevents timing-based enumeration (both paths take the same action).
        await mgr.record_failure(email)
        raise ValueError("Invalid credentials")

    if not user.is_active:
        raise ValueError("Account is inactive")

    # Successful login — reset the failure counter only after all checks pass
    await mgr.reset(email)

    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(user)
    await session.commit()
    return user


async def handle_social_login(session: AsyncSession, provider: str, user_info: dict[str, Any]) -> User:
    """Find or create a user based on social provider info."""
    email = user_info.get("email")
    if not email:
        raise ValueError(f"No email provided by {provider}")

    # 1. Try to find by Social ID
    social_id = str(user_info.get("id") or user_info.get("sub"))
    id_field = User.google_id if provider == "google" else User.github_id
    
    statement = select(User).where(id_field == social_id)
    result = await session.execute(statement)
    user = result.scalars().first()

    if user:
        user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
        # Update avatar if it changed
        new_avatar = user_info.get("picture") or user_info.get("avatar_url")
        if new_avatar:
            user.avatar_url = new_avatar
        session.add(user)
        await session.commit()
        return user

    # 2. Try to find by email (Linking)
    user = await get_user_by_email(session, email)
    if user:
        # Link existing account
        if provider == "google":
            user.google_id = social_id
        else:
            user.github_id = social_id
        
        user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
        user.is_verified = True  # Social emails are trusted
        new_avatar = user_info.get("picture") or user_info.get("avatar_url")
        if new_avatar:
            user.avatar_url = new_avatar
        session.add(user)
        await session.commit()
        return user

    # 3. Create new account (JIT)
    user = User(
        email=email,
        full_name=user_info.get("name") or user_info.get("login"),
        avatar_url=user_info.get("picture") or user_info.get("avatar_url"),
        signup_source=f"social_{provider}",
        is_verified=True,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        last_login_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    if provider == "google":
        user.google_id = social_id
    else:
        user.github_id = social_id

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user



def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, get_config().verification_key, algorithms=[ALGORITHM])
    except PyJWTError:
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