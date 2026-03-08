"""
Summarizer Service: Unified API for high-density autonomous summaries.
Exposes the modular sub-services for architecture-clean integration.
"""
from .core import (
    summarize,
    process_summarize,
    prepare_summarize_messages,
    SummarizePrepResult,
    LENGTH_PRESETS,
)
from .intelligence import (
    clean_text,
    compute_metadata,
)
from .prompts import JSON_SEP

__all__ = [
    "summarize",
    "process_summarize",
    "prepare_summarize_messages",
    "SummarizePrepResult",
    "LENGTH_PRESETS",
    "clean_text",
    "compute_metadata",
    "JSON_SEP",
]
