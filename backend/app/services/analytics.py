"""
Analytics service — aggregates reading metrics from existing tables.

No new tables needed: queries Document, FlashcardSet, ChatSession to produce
a rich analytics payload for the dashboard.

Performance: uses SQL aggregates and lightweight column projections to avoid
loading cleaned_content (up to 500 KB each) into Python memory.
"""
import logging
from collections import Counter
from datetime import datetime, date, timedelta, timezone
from urllib.parse import urlparse


from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, col

from app.models.document import Document
from app.models.flashcards import FlashcardSet, Flashcard
from app.models.chat import ChatSession, ChatMessage

logger = logging.getLogger(__name__)

# Average reading speed (words per minute) for time-saved calculation
_WPM = 200

# Approximate average word length in English (chars per word including spaces)
_AVG_CHARS_PER_WORD = 5


async def get_dashboard(user_id: int, session: AsyncSession) -> dict:
    """
    Compute all analytics for a user in a single service call.

    Returns a dict with:
      - summary_stats: total docs, words, time saved, flashcard sets, chats
      - activity_heatmap: list of {date, count} for last 365 days
      - top_domains: list of {domain, count} — top 10 sources
      - streak: current consecutive-day streak
    """

    # ---- 1. Summary stats via SQL aggregates (no content loaded) ----
    stats_stmt = (
        select(
            func.count().label("total_docs"),
            func.coalesce(func.sum(func.length(Document.cleaned_content)), 0).label("total_chars"),
        )
        .where(Document.user_id == user_id)
    )
    stats_row = (await session.execute(stats_stmt)).one()
    total_documents: int = stats_row.total_docs
    total_chars: int = stats_row.total_chars
    total_words = total_chars // _AVG_CHARS_PER_WORD
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
        .join(FlashcardSet, Flashcard.set_id == FlashcardSet.id)  # type: ignore[arg-type]
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
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)  # type: ignore[arg-type]
        .where(ChatSession.user_id == user_id)
    )
    total_chat_messages = (await session.execute(chat_msg_stmt)).scalar() or 0

    # ---- 4. Activity heatmap — last 365 days (date + count via GROUP BY) ----
    today = datetime.now(timezone.utc).date()
    year_ago = today - timedelta(days=364)

    day_col = func.date(Document.created_at).label("day")
    heatmap_stmt = (
        select(day_col, func.count().label("cnt"))
        .where(Document.user_id == user_id)
        .group_by(day_col)
    )
    heatmap_rows = (await session.execute(heatmap_stmt)).all()

    day_counts: dict[str, int] = {}
    for row in heatmap_rows:
        d = row.day
        if d is not None:
            day_str = d.isoformat() if isinstance(d, date) else str(d)[:10]
            day_counts[day_str] = row.cnt

    # Build full 365-day array (fill missing days with 0)
    heatmap = []
    for i in range(365):
        day = year_ago + timedelta(days=i)
        day_str = day.isoformat()
        heatmap.append({"date": day_str, "count": day_counts.get(day_str, 0)})

    # ---- 5. Top domains (fetch only url column — no content) ----
    url_stmt = (
        select(Document.url)
        .where(Document.user_id == user_id)
        .where(col(Document.url).isnot(None))  # type: ignore[arg-type]
    )
    url_rows = (await session.execute(url_stmt)).all()

    domain_counter: Counter = Counter()
    pasted_count = 0
    for (url,) in url_rows:
        if not url:
            continue
        if url.startswith("pasted_text"):
            pasted_count += 1
            continue
        try:
            parsed = urlparse(url)
            host = parsed.hostname or ""
            if host.startswith("www."):
                host = host[4:]
            if host:
                domain_counter[host] += 1
        except Exception:
            pass

    top_domains = [
        {"domain": domain, "count": count}
        for domain, count in domain_counter.most_common(8)
    ]
    if pasted_count > 0:
        top_domains.append({"domain": "Pasted Text", "count": pasted_count})
    top_domains.sort(key=lambda x: x["count"], reverse=True)
    top_domains = top_domains[:10]

    # ---- 6. Reading streak (reuse date counts already fetched) ----
    active_dates = sorted(
        (date.fromisoformat(ds) for ds in day_counts),
        reverse=True,
    )

    streak = 0
    if active_dates:
        check_date = today
        for active_date in active_dates:
            if active_date == check_date:
                streak += 1
                check_date -= timedelta(days=1)
            elif active_date < check_date:
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
