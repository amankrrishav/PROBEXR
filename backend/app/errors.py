"""
Structured error codes for client-side handling.

Every API error response follows the envelope:
    {"detail": str, "code": str}

Error codes are grouped by domain. Clients can switch on `code`
instead of parsing free-text `detail` strings.
"""


class ErrorCode:
    """String constants for machine-readable error codes."""

    # ── Authentication / Authorization ──────────────────────────
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_LOCKED = "AUTH_LOCKED"
    AUTH_UNVERIFIED = "AUTH_UNVERIFIED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_OAUTH_INVALID_STATE = "AUTH_OAUTH_INVALID_STATE"
    AUTH_OAUTH_FAILED = "AUTH_OAUTH_FAILED"

    # ── Rate Limiting ───────────────────────────────────────────
    RATE_LIMITED = "RATE_LIMITED"

    # ── Validation ──────────────────────────────────────────────
    INVALID_INPUT = "INVALID_INPUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # ── Resource errors ─────────────────────────────────────────
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    FORBIDDEN = "FORBIDDEN"

    # ── Service / Infrastructure ────────────────────────────────
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    LLM_ERROR = "LLM_ERROR"
    EMAIL_SEND_FAILED = "EMAIL_SEND_FAILED"

    # ── CSRF ────────────────────────────────────────────────────
    CSRF_MISSING = "CSRF_MISSING"
    CSRF_MISMATCH = "CSRF_MISMATCH"
    CSRF_ORIGIN_REJECTED = "CSRF_ORIGIN_REJECTED"

    # ── Feature flags ───────────────────────────────────────────
    FEATURE_DISABLED = "FEATURE_DISABLED"


# Map HTTP status codes to default error codes.
# Used by the global HTTPException handler when no explicit code is provided.
_STATUS_CODE_MAP: dict[int, str] = {
    400: ErrorCode.INVALID_INPUT,
    401: ErrorCode.AUTH_REQUIRED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    409: ErrorCode.CONFLICT,
    422: ErrorCode.VALIDATION_ERROR,
    429: ErrorCode.RATE_LIMITED,
    500: ErrorCode.INTERNAL_ERROR,
    503: ErrorCode.SERVICE_UNAVAILABLE,
}


def code_for_status(status_code: int) -> str:
    """Return a default error code for the given HTTP status code."""
    return _STATUS_CODE_MAP.get(status_code, ErrorCode.INTERNAL_ERROR)
