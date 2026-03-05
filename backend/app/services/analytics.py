"""
Analytics service — aggregates reading metrics from existing tables.

No new tables needed: queries Document, FlashcardSet, ChatSession to produce
a rich analytics payload for the dashboard.
"""
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.models.document import Document
from app.models.flashcards import FlashcardSet, Flashcard
from app.models.chat import ChatSession, ChatMessage

logger = logging.getLogger(__name__)

# Average reading speed (words per minute) for time-saved calculation
_WPM = 200


async def get_dashboard(user_id: int, session: AsyncSession) -> dict:
    """
    Compute all analytics for a user in a single service call.

    Returns a dict with:
      - summary_stats: total docs, words, time saved, flashcard sets, chats
      - activity_heatmap: list of {date, count} for last 365 days
      - top_domains: list of {domain, count} — top 10 sources
      - streak: current consecutive-day streak
    """

    # ---- 1. Fetch all user documents (lightweight: id, url, created_at, content length) ----
    doc_stmt = select(Document).where(Document.user_id == user_id)
    result = await session.execute(doc_stmt)
    docs = list(result.scalars().all())

    total_documents = len(docs)
    total_words = sum(len(d.cleaned_content.split()) if d.cleaned_content else 0 for d in docs)
    time_saved_seconds = int(total_words / _WPM * 60) if total_words > 0 else 0

    # ---- 2. Flashcard sets count ----
    fc_count_stmt = (
        select(func.count())
        .select_from(FlashcardSet)
        .where(FlashcardSet.user_id == user_id)
    )
    total_flashcard_sets = (await session.execute(fc_count_stmt)).scalar() or 0

    # Total individual flashcards
    fc_card_stmt = (
        select(func.count())
        .select_from(Flashcard)
        .join(FlashcardSet, Flashcard.set_id == FlashcardSet.id)
        .where(FlashcardSet.user_id == user_id)
    )
    total_flashcards = (await session.execute(fc_card_stmt)).scalar() or 0

    # ---- 3. Chat sessions count ----
    chat_count_stmt = (
        select(func.count())
        .select_from(ChatSession)
        .where(ChatSession.user_id == user_id)
    )
    total_chat_sessions = (await session.execute(chat_count_stmt)).scalar() or 0

    # Total chat messages
    chat_msg_stmt = (
        select(func.count())
        .select_from(ChatMessage)
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.user_id == user_id)
    )
    total_chat_messages = (await session.execute(chat_msg_stmt)).scalar() or 0

    # ---- 4. Activity heatmap — last 365 days ----
    today = datetime.now(timezone.utc).date()
    year_ago = today - timedelta(days=364)

    # Group documents by creation date
    day_counts: dict[str, int] = defaultdict(int)
    for d in docs:
        if d.created_at:
            day_str = d.created_at.date().isoformat() if hasattr(d.created_at, 'date') else str(d.created_at)[:10]
            day_counts[day_str] += 1

    # Build full 365-day array (fill missing days with 0)
    heatmap = []
    for i in range(365):
        day = year_ago + timedelta(days=i)
        day_str = day.isoformat()
        heatmap.append({"date": day_str, "count": day_counts.get(day_str, 0)})

    # ---- 5. Top domains ----
    domain_counter: Counter = Counter()
    for d in docs:
        if d.url and d.url != "pasted_text":
            try:
                parsed = urlparse(d.url)
                host = parsed.hostname or ""
                # Strip www.
                if host.startswith("www."):
                    host = host[4:]
                if host:
                    domain_counter[host] += 1
            except Exception:
                pass
    # Add pasted text count separately
    pasted_count = sum(1 for d in docs if d.url == "pasted_text")

    top_domains = [
        {"domain": domain, "count": count}
        for domain, count in domain_counter.most_common(8)
    ]
    if pasted_count > 0:
        top_domains.append({"domain": "Pasted Text", "count": pasted_count})
    # Sort by count descending, take top 10
    top_domains.sort(key=lambda x: x["count"], reverse=True)
    top_domains = top_domains[:10]

    # ---- 6. Reading streak ----
    active_dates = sorted(set(
        d.created_at.date() if hasattr(d.created_at, 'date') else d.created_at
        for d in docs if d.created_at
    ), reverse=True)

    streak = 0
    if active_dates:
        check_date = today
        for active_date in active_dates:
            if active_date == check_date:
                streak += 1
                check_date -= timedelta(days=1)
            elif active_date < check_date:
                # Gap found — streak broken
                break

    # ---- Build response ----
    return {
        "summary_stats": {
            "total_documents": total_documents,
            "total_words": total_words,
            "time_saved_seconds": time_saved_seconds,
            "total_flashcard_sets": total_flashcard_sets,
            "total_flashcards": total_flashcards,
            "total_chat_sessions": total_chat_sessions,
            "total_chat_messages": total_chat_messages,
        },
        "activity_heatmap": heatmap,
        "top_domains": top_domains,
        "streak": streak,
    }
