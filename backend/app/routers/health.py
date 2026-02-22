from fastapi import APIRouter
from app.config import get_config

router = APIRouter(tags=["health"])


def _has_llm_provider(cfg) -> bool:
    return bool(cfg.groq_api_key or cfg.openai_api_key or cfg.openrouter_api_key)


@router.get("/")
def health():
    cfg = get_config()
    mode = cfg.summarize_provider if _has_llm_provider(cfg) else "extractive"
    return {
        "status": f"{cfg.app_name} running",
        "mode": mode or "extractive",
        "note": "extractive = free, no API key. Set GROQ_API_KEY (free) for better summaries.",
    }
