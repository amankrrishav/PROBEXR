"""
App configuration from environment. Safe for serverless (no heavy imports).
Add new keys here as you add features.
"""
import os
from functools import lru_cache
from typing import Literal

ProviderName = Literal["groq", "openai", "openrouter"]


def _env(key: str, default: str | None = None) -> str | None:
    v = os.environ.get(key)
    return (v.strip() if v else None) or default


@lru_cache
def get_config() -> "AppConfig":
    return AppConfig()


class AppConfig:
    """Configuration loaded from env."""

    def __init__(self) -> None:
        # App
        self.app_name = _env("APP_NAME", "ReadPulse") or "ReadPulse"
        self.debug = (_env("DEBUG", "0") or "0").lower() in ("1", "true", "yes")

        # CORS (comma-separated origins, or *)
        self.cors_origins = _env("CORS_ORIGINS", "*") or "*"

        # Summarization: provider auto-detected from API keys
        self.summarize_provider: ProviderName | None = _env("SUMMARIZE_PROVIDER") or None  # type: ignore
        self.summarize_model = _env("SUMMARIZE_MODEL", "") or ""
        self.summarize_timeout_seconds = int(_env("SUMMARIZE_TIMEOUT", "90") or "90")

        # Groq (free tier) — https://console.groq.com
        self.groq_api_key = _env("GROQ_API_KEY")
        self.groq_base_url = _env("GROQ_BASE_URL", "https://api.groq.com/openai/v1") or "https://api.groq.com/openai/v1"

        # OpenAI
        self.openai_api_key = _env("OPENAI_API_KEY")
        self.openai_base_url = _env("OPENAI_BASE_URL", "https://api.openai.com/v1") or "https://api.openai.com/v1"

        # OpenRouter (free tier models available)
        self.openrouter_api_key = _env("OPENROUTER_API_KEY")
        self.openrouter_base_url = _env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1") or "https://openrouter.ai/api/v1"

        # Validation
        self.min_words = int(_env("SUMMARIZE_MIN_WORDS", "30") or "30")
        self.target_min_words = int(_env("SUMMARIZE_TARGET_MIN_WORDS", "80") or "80")
        self.target_max_words = int(_env("SUMMARIZE_TARGET_MAX_WORDS", "300") or "300")

        # ----- Future: subscription / plans (add keys here when you add billing) -----
        self.app_version = _env("APP_VERSION", "1.0.0") or "1.0.0"
        self.subscription_enabled = (_env("SUBSCRIPTION_ENABLED", "0") or "0").lower() in ("1", "true", "yes")
        self.free_daily_limit = int(_env("FREE_DAILY_LIMIT", "50") or "50")  # per IP or per user when auth exists

        # When auth exists: API_KEY_HEADER, JWT_SECRET, STRIPE_WEBHOOK_SECRET, etc. #new
        self.SECRET_KEY = _env("SECRET_KEY", "dev-secret-change-this") or "dev-secret-change-this"
        self.ALGORITHM = _env("JWT_ALGORITHM", "HS256") or "HS256"


        # Resolve provider and default model if not set
        if not self.summarize_provider:
            if self.groq_api_key:
                self.summarize_provider = "groq"
                if not self.summarize_model:
                    self.summarize_model = _env("GROQ_MODEL", "llama-3.3-70b-versatile") or "llama-3.3-70b-versatile"
            elif self.openai_api_key:
                self.summarize_provider = "openai"
                if not self.summarize_model:
                    self.summarize_model = _env("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini"
            elif self.openrouter_api_key:
                self.summarize_provider = "openrouter"
                if not self.summarize_model:
                    self.summarize_model = _env("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free") or "meta-llama/llama-3.1-8b-instruct:free"

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
            return self.groq_api_key
        if self.summarize_provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY is not set.")
            return self.openai_api_key
        if self.summarize_provider == "openrouter":
            if not self.openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY is not set.")
            return self.openrouter_api_key
        raise ValueError("No LLM provider configured. Set one of GROQ_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY.")
