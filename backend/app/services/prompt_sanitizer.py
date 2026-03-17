"""
app/services/prompt_sanitizer.py  —  A-13: Prompt injection sanitizer.

Strips / neutralises instruction-override patterns from user-controlled
text before it is injected into LLM prompts.

Design
------
* Defensive-in-depth: we are NOT trying to build a perfect filter (that is
  impossible).  The goal is to raise the bar significantly so casual
  injection attempts embedded in pasted articles or user instructions fail.
* Zero false-positive risk for normal content: only patterns that are
  unambiguous instruction-override attempts are removed.
* Two public functions:
    sanitize_document_content(text)  — aggressive; for article / doc text
                                       injected into the system prompt.
    sanitize_user_prompt(text)       — lighter; for explicit user instructions
                                       (synthesis custom prompt, etc.).

Injection pattern families covered
-----------------------------------
  • "Ignore / disregard / bypass / override [all] [previous|above|…] instructions"
  • "Forget everything / forget all / forget what you were told"
  • "You are now a … / Act as a … / Pretend you are …"
  • "Your new instructions are … / New task: / New instructions:"
  • Inline system-prompt override: "System:" / "System prompt:" at line start
  • "Do not follow [the] [above|previous] instructions"
  • DAN / jailbreak keywords
  • Prompt-leak attempts: "repeat your system prompt", "print the above instructions"
  • Role-play escape: "END OF INSTRUCTIONS" / "STOP YOUR INSTRUCTIONS"
  • "From now on you are / ignore …"
  • (doc only) XML-style instruction tags: <system>, <instruction>, <prompt>
  • (doc only) Markdown instruction headers: "## New Instructions"
"""

import re
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Replacement token
# ---------------------------------------------------------------------------
_REDACT = "[REMOVED]"

# ---------------------------------------------------------------------------
# Base patterns — applied by BOTH sanitize_document_content and sanitize_user_prompt
# ---------------------------------------------------------------------------
_BASE_PATTERNS: list[tuple[re.Pattern[str], str]] = [

    # "ignore / disregard / bypass / override [all] [the] [previous|above|…] instructions"
    (re.compile(
        r"\b(ignore|disregard|bypass|override)\s+(all\s+)?"
        r"(the\s+|a\s+|an\s+)?"
        r"(previous|prior|above|earlier|existing|your|original)?\s*"
        r"(instructions?|prompts?|context|rules?|constraints?|guidelines?|system\s+prompt)\b",
        re.IGNORECASE,
    ), _REDACT),

    # "forget everything / forget all instructions / forget what you were told"
    (re.compile(
        r"\bforget\s+(everything|all|what\s+you|your\s+(previous|prior|above|earlier)"
        r"|the\s+(above|previous|prior|instructions?))\b",
        re.IGNORECASE,
    ), _REDACT),

    # "you are now a … / act as a … / pretend (you are|to be) …"
    (re.compile(
        r"\b(you\s+are\s+now\s+(a|an)|act\s+as\s+(a|an)|pretend\s+(you\s+are|to\s+be))\b",
        re.IGNORECASE,
    ), _REDACT),

    # "your new instructions are / new task: / new instructions:"
    (re.compile(
        r"\b(your\s+new\s+instructions?\s+(are|is)|new\s+(task|instructions?|prompt)\s*:)",
        re.IGNORECASE,
    ), _REDACT),

    # "System:" or "System prompt:" at the start of a line
    (re.compile(
        r"(?m)^\s*system\s*(prompt)?\s*:",
        re.IGNORECASE,
    ), _REDACT),

    # "do not follow [the] [above|previous|…] instructions"
    (re.compile(
        r"\bdo\s+not\s+follow\s+(the\s+)?(above|previous|prior|original|your)?\s*"
        r"(instructions?|prompts?|rules?|guidelines?)?\b",
        re.IGNORECASE,
    ), _REDACT),

    # DAN / jailbreak keywords
    (re.compile(
        r"\b(jailbreak|do\s+anything\s+now|DAN\b)",
        re.IGNORECASE,
    ), _REDACT),

    # Prompt-leak attempts: "repeat your system prompt", "print the above instructions"
    (re.compile(
        r"\b(repeat|print|show|reveal|output|display|return|give\s+me|tell\s+me)\s+"
        r"(me\s+)?(the\s+|your\s+)?(system\s+prompt|above\s+instructions?|previous\s+instructions?"
        r"|original\s+prompt|full\s+prompt|initial\s+instructions?)\b",
        re.IGNORECASE,
    ), _REDACT),

    # Role-play escape: "END OF INSTRUCTIONS" / "STOP YOUR INSTRUCTIONS"
    (re.compile(
        r"\b(end|stop)\s+(of\s+)?(your\s+)?(instructions?|prompt|context|rules?)\b",
        re.IGNORECASE,
    ), _REDACT),

    # "From now on you are / ignore / act …"
    (re.compile(
        r"\bfrom\s+now\s+on\s+(you\s+(are|will|must|should)|ignore|disregard|act)\b",
        re.IGNORECASE,
    ), _REDACT),
]

# ---------------------------------------------------------------------------
# Document-content-only extra patterns
# (more aggressive; not applied to short user instruction strings)
# ---------------------------------------------------------------------------
_DOC_EXTRA_PATTERNS: list[tuple[re.Pattern[str], str]] = [

    # XML-style instruction delimiters sometimes used to smuggle context switches
    (re.compile(
        r"<\s*/?\s*(system|instruction|prompt|task)\s*>",
        re.IGNORECASE,
    ), _REDACT),

    # Markdown "## New Instructions" / "# System Prompt" section headers inside content
    (re.compile(
        r"(?m)^#{1,3}\s*(new\s+instructions?|system\s+prompt|ignore\s+above)\s*$",
        re.IGNORECASE,
    ), _REDACT),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sanitize_document_content(text: str) -> str:
    """
    Sanitize article / document text before it is embedded in an LLM system prompt.

    Applies all base patterns plus the stricter document-specific extras.
    Logs a warning whenever content is modified so suspicious inputs are
    visible in production logs.
    """
    if not text:
        return text

    original = text
    for pattern, replacement in _BASE_PATTERNS + _DOC_EXTRA_PATTERNS:
        text = pattern.sub(replacement, text)

    if text != original:
        logger.warning(
            "prompt_sanitizer: document content modified — possible injection attempt. "
            "original_len=%d sanitized_len=%d",
            len(original), len(text),
        )
    return text


def sanitize_user_prompt(text: str) -> str:
    """
    Sanitize an explicit user-supplied instruction string (e.g. the synthesis
    custom prompt field).

    Applies only the base patterns — we are more conservative here because
    legitimate user instructions are short and intentional.
    """
    if not text:
        return text

    original = text
    for pattern, replacement in _BASE_PATTERNS:
        text = pattern.sub(replacement, text)

    if text != original:
        logger.warning(
            "prompt_sanitizer: user prompt modified — possible injection attempt. "
            "original_len=%d sanitized_len=%d",
            len(original), len(text),
        )
    return text