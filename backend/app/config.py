"""
App configuration from environment using pydantic-settings BaseSettings.
All fields have the same names, defaults, and behavior as the original config.
"""
from functools import lru_cache
from typing import Literal, Optional
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ProviderName = Literal["groq", "openai", "openrouter"]


class AppConfig(BaseSettings):
    """Configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────
    app_name: str = "PROBEXR"
    debug: bool = False
    environment: str = "development"
    app_version: str = "1.0.0"

    # ── CORS ─────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    # ── Summarization ────────────────────────────────────────────
    summarize_provider: Optional[ProviderName] = None
    summarize_model: str = ""
    summarize_timeout_seconds: int = 90

    # ── Groq ─────────────────────────────────────────────────────
    groq_api_key: Optional[str] = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"

    # ── OpenAI ───────────────────────────────────────────────────
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # ── OpenRouter ───────────────────────────────────────────────
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "meta-llama/llama-3.1-8b-instruct:free"

    # ── Validation ───────────────────────────────────────────────
    min_words: int = 30
    target_min_words: int = 80
    target_max_words: int = 300

    # ── Database ─────────────────────────────────────────────────
    database_url: str = "sqlite:///./probefy.db"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    # ── OAuth2 ───────────────────────────────────────────────────
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    frontend_url: str = "http://localhost:5173"

    # ── Email / SMTP (SendGrid, SES, Resend, etc.) ───────────────
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: str = "noreply@probexr.com"

    # ── Auth / JWT ───────────────────────────────────────────────
    secret_key: str = "dev-secret-change-this"
    algorithm: str = "HS256"
    # RS256 readiness: set these + algorithm="RS256" to switch to asymmetric JWTs.
    # Values are PEM-encoded keys (include \n literals or use multi-line env vars).
    jwt_private_key: Optional[str] = None   # Used for signing (auth service only)
    jwt_public_key: Optional[str] = None    # Used for verification (can be shared with other services)

    # ── Rate Limiting ────────────────────────────────────────────
    rate_limit_per_minute: int = 60
    rate_limit_llm_per_minute: int = 10
    rate_limit_auth_per_minute: int = 5  # Tight limit for login/register/magic-link

    # ── Account Lockout ──────────────────────────────────────────
    lockout_max_attempts: int = 5        # Failed logins before lockout
    lockout_window_seconds: int = 900    # 15 minutes

    # ── Token Lifetimes ──────────────────────────────────────────
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # ── Redis ────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Aliases for backward compatibility ───────────────────────
    # The old config exposed these as cfg.SECRET_KEY and cfg.ALGORITHM.
    # We keep them as computed properties so existing code doesn't break.
    @property
    def SECRET_KEY(self) -> str:  # noqa: N802
        return self.secret_key

    @property
    def ALGORITHM(self) -> str:  # noqa: N802
        return self.algorithm

    @property
    def signing_key(self) -> str:
        """Key used for JWT signing — private key for RS256, secret_key for HS256."""
        if self.algorithm.startswith("RS") or self.algorithm.startswith("ES"):
            if not self.jwt_private_key:
                raise RuntimeError(
                    f"algorithm={self.algorithm} requires jwt_private_key to be set"
                )
            return self.jwt_private_key
        return self.secret_key

    @property
    def verification_key(self) -> str:
        """Key used for JWT verification — public key for RS256, secret_key for HS256."""
        if self.algorithm.startswith("RS") or self.algorithm.startswith("ES"):
            if not self.jwt_public_key:
                raise RuntimeError(
                    f"algorithm={self.algorithm} requires jwt_public_key to be set"
                )
            return self.jwt_public_key
        return self.secret_key

    # ── Provider auto-detection ──────────────────────────────────
    @model_validator(mode="after")
    def _resolve_provider_and_model(self) -> "AppConfig":
        """If no explicit provider is set, detect from available API keys."""
        if not self.summarize_provider:
            if self.groq_api_key:
                self.summarize_provider = "groq"
                if not self.summarize_model:
                    self.summarize_model = self.groq_model
            elif self.openai_api_key:
                self.summarize_provider = "openai"
                if not self.summarize_model:
                    self.summarize_model = self.openai_model
            elif self.openrouter_api_key:
                self.summarize_provider = "openrouter"
                if not self.summarize_model:
                    self.summarize_model = self.openrouter_model
        return self

    # ── LLM helpers ──────────────────────────────────────────────
    def get_llm_base_url(self) -> str:
        if self.summarize_provider == "groq":
            return self.groq_base_url
        if self.summarize_provider == "openai":
            return self.openai_base_url
        if self.summarize_provider == "openrouter":
            return self.openrouter_base_url
        raise ValueError("No LLM provider configured. Set GROQ_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY.")

    def get_llm_api_key(self) -> str:
        if self.summarize_provider == "groq":
            if not self.groq_api_key:
                raise ValueError("GROQ_API_KEY is not set.")
            return str(self.groq_api_key)
        if self.summarize_provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY is not set.")
            return str(self.openai_api_key)
        if self.summarize_provider == "openrouter":
            if not self.openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY is not set.")
            return str(self.openrouter_api_key)
        raise ValueError("No LLM provider configured. Set one of GROQ_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY.")

    @property
    def has_llm_provider(self) -> bool:
        return bool(self.groq_api_key or self.openai_api_key or self.openrouter_api_key)

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.database_url.lower()

    @property
    def async_database_url(self) -> str:
        """Convert DATABASE_URL to async driver variant with robust cloud fixes."""
        url = self.database_url
        if not url:
            return ""

        # 1. Normalise driver prefixes
        is_cloud = any(x in url for x in ["cockroachlabs.cloud", "render.com", "amazonaws.com"])
        if url.startswith("sqlite:///"):
            url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        elif url.startswith("postgresql://") or url.startswith("postgres://"):
            prefix = "postgresql"
            if is_cloud:
                prefix = "cockroachdb"
            url = url.replace("postgresql://", f"{prefix}+asyncpg://", 1)
            url = url.replace("postgres://", f"{prefix}+asyncpg://", 1)

        # 2. Aggressive Purification for Cloud/CockroachDB
        if self.is_sqlite:
            return url

        try:
            u = urlparse(url)
            q = parse_qs(u.query)

            # Remove junk that causes driver failures if local files are missing
            for k in ["sslrootcert", "sslcert", "sslkey"]:
                q.pop(k, None)

            # Ensure we strip sslmode for asyncpg (handled in connect_args)
            q.pop("sslmode", None)

            u = u._replace(query=urlencode(q, doseq=True))
            url = urlunparse(u)
        except Exception:
            # Fallback to original if parsing fails
            pass

        return url


@lru_cache
def get_config() -> AppConfig:
    return AppConfig()