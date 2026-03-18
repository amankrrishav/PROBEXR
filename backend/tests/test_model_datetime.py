"""
tests/test_model_datetime.py — N-05: datetime.utcnow() replaced in all models

Python 3.12 deprecates datetime.utcnow() with a DeprecationWarning.
All model created_at fields must use datetime.now(timezone.utc).replace(tzinfo=None).
"""
import inspect


AFFECTED_MODELS = [
    ("app.models.chat", "ChatSession"),
    ("app.models.chat", "ChatMessage"),
    ("app.models.flashcards", "FlashcardSet"),
    ("app.models.synthesis", "Synthesis"),
    ("app.models.tts", "AudioSummary"),
]


def _get_model_source(module_path: str) -> str:
    import importlib
    mod = importlib.import_module(module_path)
    return inspect.getsource(mod)


def test_chat_model_no_utcnow():
    src = _get_model_source("app.models.chat")
    assert "utcnow()" not in src, (
        "app/models/chat.py must not use datetime.utcnow() — deprecated in Python 3.12"
    )


def test_flashcards_model_no_utcnow():
    src = _get_model_source("app.models.flashcards")
    assert "utcnow()" not in src, (
        "app/models/flashcards.py must not use datetime.utcnow()"
    )


def test_synthesis_model_no_utcnow():
    src = _get_model_source("app.models.synthesis")
    assert "utcnow()" not in src, (
        "app/models/synthesis.py must not use datetime.utcnow()"
    )


def test_tts_model_no_utcnow():
    src = _get_model_source("app.models.tts")
    assert "utcnow()" not in src, (
        "app/models/tts.py must not use datetime.utcnow()"
    )


def test_all_models_use_timezone_utc():
    """All affected models must use datetime.now(timezone.utc) pattern."""
    for module_path, class_name in AFFECTED_MODELS:
        src = _get_model_source(module_path)
        assert "timezone.utc" in src, (
            f"{module_path} must use datetime.now(timezone.utc) for created_at"
        )