from app.schemas.requests import TextRequest
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    Token,
    UserRead,
    MagicLinkRequest,
    ProfileUpdate,
    PasswordResetRequest,
    PasswordResetConfirm,
    ResendVerificationRequest,
)

__all__ = [
    "TextRequest",
    "LoginRequest",
    "RegisterRequest",
    "Token",
    "UserRead",
    "MagicLinkRequest",
    "ProfileUpdate",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "ResendVerificationRequest",
]