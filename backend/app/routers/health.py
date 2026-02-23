from fastapi import APIRouter

from app.config import get_config

router = APIRouter(tags=["health"])


def _has_llm_provider(cfg) -> bool:
    return bool(cfg.groq_api_key or cfg.openai_api_key or cfg.openrouter_api_key)


@router.get("/")
def health():
    """Public health + capabilities. Frontend can show mode, version; later: plan, limits."""
    cfg = get_config()
    mode = cfg.summarize_provider if _has_llm_provider(cfg) else "extractive"
    return {
        "status": f"{cfg.app_name} running",
        "version": cfg.app_version,
        "mode": mode or "extractive",
        "capabilities": ["summarize"],
        "subscription_enabled": cfg.subscription_enabled,
        "free_daily_limit": cfg.free_daily_limit,
        "plans": ["free", "pro"],
        "note": "extractive = free, no API key. Set GROQ_API_KEY (free) for better summaries.",
    }
