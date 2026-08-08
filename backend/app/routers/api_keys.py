"""API key router — create, list, and revoke API keys for programmatic access."""
import hashlib
import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from app.deps import DbSession, VerifiedUser
from app.models.api_key import APIKey
from app.services.audit import record_audit_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class CreateKeyRequest(BaseModel):
    name: str


class CreateKeyResponse(BaseModel):
    id: int
    name: str
    prefix: str
    key: str  # plaintext — shown only once


class KeyInfo(BaseModel):
    id: int
    name: str
    prefix: str
    created_at: str
    last_used_at: str | None
    is_active: bool


@router.post("/", response_model=CreateKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateKeyRequest,
    user: VerifiedUser,
    session: DbSession,
) -> CreateKeyResponse:
    """Create a new API key. The plaintext key is returned ONCE — store it securely."""
    if user.id is None:
        raise HTTPException(status_code=500, detail="User lookup failed")

    raw_key = APIKey.generate_key()
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    api_key = APIKey(
        user_id=user.id,
        name=request.name[:100],
        key_hash=key_hash,
        prefix=raw_key[:16],
    )
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)

    record_audit_event(
        "api_key_created",
        user=user,
        detail={"info": f"API key '{request.name}' created (prefix: {raw_key[:16]})"},
    )

    logger.info("API key created: user_id=%s prefix=%s", user.id, raw_key[:16])
    return CreateKeyResponse(
        id=api_key.id,  # type: ignore[arg-type]
        name=api_key.name,
        prefix=api_key.prefix,
        key=raw_key,
    )


@router.get("/", response_model=list[KeyInfo])
async def list_api_keys(
    user: VerifiedUser,
    session: DbSession,
) -> list[KeyInfo]:
    """List all API keys for the current user (without the secret)."""
    if user.id is None:
        raise HTTPException(status_code=500, detail="User lookup failed")

    result = await session.execute(
        select(APIKey).where(APIKey.user_id == user.id).order_by(APIKey.created_at.desc())  # type: ignore[attr-defined]
    )
    keys = result.scalars().all()

    return [
        KeyInfo(
            id=k.id,  # type: ignore[arg-type]
            name=k.name,
            prefix=k.prefix,
            created_at=k.created_at.isoformat() if k.created_at else "",
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            is_active=k.is_active,
        )
        for k in keys
    ]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    user: VerifiedUser,
    session: DbSession,
) -> None:
    """Revoke (deactivate) an API key."""
    if user.id is None:
        raise HTTPException(status_code=500, detail="User lookup failed")

    api_key = await session.get(APIKey, key_id)
    if not api_key or api_key.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    api_key.is_active = False
    session.add(api_key)
    await session.commit()

    record_audit_event(
        "api_key_revoked",
        user=user,
        detail={"info": f"API key \'{api_key.name}\' revoked (prefix: {api_key.prefix})"},
    )
    logger.info("API key revoked: user_id=%s key_id=%s", user.id, key_id)
