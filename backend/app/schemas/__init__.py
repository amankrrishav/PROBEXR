from app.schemas.auth import (
    LoginRequest,
    MagicLinkRequest,
    OAuthCallbackRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    ProfileUpdate,
    RegisterRequest,
    ResendVerificationRequest,
    Token,
    UserRead,
)
from app.schemas.requests import TextRequest

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
    "OAuthCallbackRequest",
]
