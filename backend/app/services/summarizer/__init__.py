"""
Summarizer Service: Unified API for high-density autonomous summaries.
Exposes the modular sub-services for architecture-clean integration.
"""

from .core import (
    LENGTH_PRESETS,
    SummarizePrepResult,
    parse_takeaways,
    prepare_summarize_messages,
    process_summarize,
    summarize,
)
from .intelligence import (
    clean_text,
    compute_metadata,
)

__all__ = [
    "summarize",
    "process_summarize",
    "prepare_summarize_messages",
    "SummarizePrepResult",
    "LENGTH_PRESETS",
    "parse_takeaways",
    "clean_text",
    "compute_metadata",
]
