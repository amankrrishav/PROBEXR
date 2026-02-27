from fastapi import APIRouter

from app.config import get_config

router = APIRouter(tags=["health"])


from typing import Any

@router.get("/")
def health() -> dict[str, Any]:
    """Public health + capabilities. Frontend can show mode, version; later: plan, limits."""
    cfg = get_config()
    mode = cfg.summarize_provider if cfg.has_llm_provider else "extractive"
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
