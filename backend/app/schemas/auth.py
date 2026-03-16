from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Password policy — applied on RegisterRequest and PasswordResetConfirm.
# Rules (NIST SP 800-63B + OWASP):
#   • 12–128 characters
#   • At least 1 uppercase, 1 lowercase, 1 digit, 1 special character
#   • Not a known-common password
# ---------------------------------------------------------------------------

_MIN_PASSWORD_LENGTH = 12
_MAX_PASSWORD_LENGTH = 128

_SPECIAL_CHARS = set("!@#$%^&*()_+-=[]{}|;:',.<>?/~`\"\\")

_COMMON_PASSWORDS = {
    "password", "password1", "password12", "password123",
    "12345678", "123456789", "1234567890", "qwerty123",
    "iloveyou", "sunshine", "princess", "letmein1",
    "welcome1", "monkey123", "dragon123", "master123",
    "passw0rd", "pass1234", "abc12345", "admin1234",
}


def _validate_password_strength(password: str) -> str:
    """Shared password strength validator — raises ValueError on failure."""
    import re
    if len(password) < _MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {_MIN_PASSWORD_LENGTH} characters long."
        )
    if len(password) > _MAX_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be no longer than {_MAX_PASSWORD_LENGTH} characters."
        )
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not any(c.islower() for c in password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one digit.")
    if not any(c in _SPECIAL_CHARS for c in password):
        raise ValueError(
            "Password must contain at least one special character "
            "(!@#$%^&*()_+-=[]{}|;:',.<>?/~`\"\\)."
        )
    # Strip punctuation/spaces before common-password check so that
    # "Password123!" is still caught as a variant of "password123".
    base = re.sub(r"[^a-z0-9]", "", password.lower())
    if base in _COMMON_PASSWORDS:
        raise ValueError("Password is too common. Please choose a stronger password.")
    return password


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=_MIN_PASSWORD_LENGTH, max_length=_MAX_PASSWORD_LENGTH)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str  # No policy check on login — never leak policy details via login errors


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MagicLinkRequest(BaseModel):
    email: EmailStr


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=_MIN_PASSWORD_LENGTH, max_length=_MAX_PASSWORD_LENGTH)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class ResendVerificationRequest(BaseModel):
    email: EmailStr