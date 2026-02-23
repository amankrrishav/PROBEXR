import httpx
from fastapi import APIRouter, HTTPException, Depends

from app.config import get_config
from app.deps import OptionalUser
from app.schemas import TextRequest
from app.services.summarizer import summarize
from app.services.subscription import evaluate_summary_quality
from app.db import get_session
from sqlmodel import Session

router = APIRouter(prefix="", tags=["summarize"])


@router.post("/summarize")
async def summarize_endpoint(
    request: TextRequest,
    user: OptionalUser,
    session: Session = Depends(get_session),
):
    text = request.text.strip()
    cfg = get_config()

    if not text:
        raise HTTPException(status_code=400, detail="Text is required.")

    if len(text.split()) < cfg.min_words:
        raise HTTPException(
            status_code=400,
            detail=f"Text too short. Minimum {cfg.min_words} words.",
        )

    try:
        quality, usage_today, limit = evaluate_summary_quality(user, session)
        summary = await summarize(text, quality=quality)
        return {
          "summary": summary,
          "quality": quality,
          "usage_today": usage_today,
          "limit": limit,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPStatusError as e:
        msg = str(e)
        if "timed out" in msg.lower() or e.response.status_code == 504:
            raise HTTPException(status_code=504, detail="Summarization timed out. Try a shorter text.")
        if e.response.status_code == 401:
            raise HTTPException(status_code=503, detail="Summarization service misconfigured. Check API key.")
        if e.response.status_code == 429:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a moment.")
        try:
            body = e.response.json()
            err = body.get("error", body.get("message", msg))
            if isinstance(err, dict):
                err = err.get("message", str(err))
            msg = str(err)
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=msg or "Summarization failed.")
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach summarization service. Check your network and API key.",
        )
