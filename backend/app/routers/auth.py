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
    MagicLinkRequest,
    ProfileUpdate,
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
    handle_social_login,
    create_magic_link_token,
    verify_magic_link_token,
)
from app.services.social import get_google_user_info, get_github_user_info
from app.services.email import send_magic_link_email
from app.config import get_config
from fastapi.responses import RedirectResponse
import jwt
from datetime import timedelta


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

    assert user.id is not None
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

    assert user.id is not None
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


# --- Social Login (Google) ---

@router.get("/google/login")
async def google_login(response: Response):
    cfg = get_config()
    state_payload = {"provider": "google", "exp": datetime.now(timezone.utc) + timedelta(minutes=10)}
    state_token = jwt.encode(state_payload, cfg.secret_key, algorithm=cfg.algorithm)
    
    # Store state token in an HttpOnly cookie to verify during callback
    is_prod = cfg.environment == "production"
    response.set_cookie(
        key="oauth_state",
        value=state_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=600,
        path="/api/v1/auth"
    )

    params = {
        "client_id": cfg.google_client_id,
        "redirect_uri": f"{cfg.frontend_url}/auth/callback/google",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": state_token,
    }
    from urllib.parse import urlencode
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url)


@router.post("/google/callback", response_model=Token)
async def google_callback(
    request: Request,
    response: Response,
    session: DbSession
) -> Token:
    body = await request.json()
    code = body.get("code")
    state = body.get("state")
    
    if not code:
        raise HTTPException(status_code=400, detail="Code missing")

    # Validate state CSRF parameter
    cookie_state = request.cookies.get("oauth_state")
    if not state or not cookie_state or state != cookie_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state (CSRF possible)")
    
    cfg = get_config()
    try:
        # Verify state is valid and hasn't expired
        jwt.decode(state, cfg.secret_key, algorithms=[cfg.algorithm])
    except Exception:
        raise HTTPException(status_code=400, detail="OAuth state expired or invalid")
    
    response.delete_cookie("oauth_state", path="/api/v1/auth")

    cfg = get_config()
    try:
        user_info = await get_google_user_info(code, f"{cfg.frontend_url}/auth/callback/google")
        user = await handle_social_login(session, "google", user_info)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    assert user.id is not None
    access_token = create_access_token({"sub": user.email})
    refresh = await create_refresh_token(session, user.id)

    set_auth_cookie(response, access_token)
    set_refresh_cookie(response, refresh.token)
    return Token(access_token=access_token, refresh_token=refresh.token)


# --- Social Login (GitHub) ---

@router.get("/github/login")
async def github_login(response: Response):
    cfg = get_config()
    state_payload = {"provider": "github", "exp": datetime.now(timezone.utc) + timedelta(minutes=10)}
    state_token = jwt.encode(state_payload, cfg.secret_key, algorithm=cfg.algorithm)
    
    is_prod = cfg.environment == "production"
    response.set_cookie(
        key="oauth_state",
        value=state_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=600,
        path="/api/v1/auth"
    )

    params = {
        "client_id": cfg.github_client_id,
        "scope": "user:email",
        "state": state_token,
    }
    from urllib.parse import urlencode
    url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    return RedirectResponse(url)


@router.post("/github/callback", response_model=Token)
async def github_callback(
    request: Request,
    response: Response,
    session: DbSession
) -> Token:
    body = await request.json()
    code = body.get("code")
    state = body.get("state")
    
    if not code:
        raise HTTPException(status_code=400, detail="Code missing")

    cookie_state = request.cookies.get("oauth_state")
    if not state or not cookie_state or state != cookie_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state (CSRF possible)")
        
    cfg = get_config()
    try:
        jwt.decode(state, cfg.secret_key, algorithms=[cfg.algorithm])
    except Exception:
        raise HTTPException(status_code=400, detail="OAuth state expired or invalid")
        
    response.delete_cookie("oauth_state", path="/api/v1/auth")

    try:
        user_info = await get_github_user_info(code)
        # Note: GitHub doesn't strictly need redirect_uri for token exchange 
        # but we use frontend_url consistently.
        user = await handle_social_login(session, "github", user_info)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    assert user.id is not None
    access_token = create_access_token({"sub": user.email})
    refresh = await create_refresh_token(session, user.id)

    set_auth_cookie(response, access_token)
    set_refresh_cookie(response, refresh.token)
    return Token(access_token=access_token, refresh_token=refresh.token)


# --- Magic Links (Phase 3) ---

@router.post("/magic-link")
async def request_magic_link(payload: MagicLinkRequest):
    token = create_magic_link_token(payload.email)
    cfg = get_config()
    magic_link = f"{cfg.frontend_url}/auth/verify?token={token}"
    
    try:
        await send_magic_link_email(payload.email, magic_link)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
    
    return {"message": "Magic link sent! Check your email (or server logs in Dev Mode)."}


@router.get("/verify", response_model=Token)
async def verify_magic_link(
    token: str,
    response: Response,
    session: DbSession
) -> Token:
    try:
        user = await verify_magic_link_token(session, token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    assert user.id is not None
    access_token = create_access_token({"sub": user.email})
    refresh = await create_refresh_token(session, user.id)

    set_auth_cookie(response, access_token)
    set_refresh_cookie(response, refresh.token)
    return Token(access_token=access_token, refresh_token=refresh.token)


# --- Profile (Phase 4) ---

@router.put("/me", response_model=UserRead)
async def update_profile(
    payload: ProfileUpdate,
    current_user: CurrentUser,
    session: DbSession
) -> UserRead:
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url
    
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return UserRead.model_validate(current_user)


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
    assert current_user.id is not None
    count = await revoke_all_user_tokens(session, current_user.id)
    delete_auth_cookies(response)
    return {"message": f"Logged out of all sessions ({count} tokens revoked)"}


@router.get("/me", response_model=UserRead)
async def read_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
