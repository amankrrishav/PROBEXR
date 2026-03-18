"""
tests/test_tts_schema.py — N-04: TTSRequest.provider Literal validation

TTSRequest had no test coverage anywhere in the suite.
The provider field was an unvalidated str — now a Literal enum.
"""
import pytest
import pydantic
from app.schemas.requests import TTSRequest


def test_provider_accepts_openai():
    req = TTSRequest(document_id=1, provider="openai")
    assert req.provider == "openai"


def test_provider_accepts_elevenlabs():
    req = TTSRequest(document_id=1, provider="elevenlabs")
    assert req.provider == "elevenlabs"


def test_provider_default_is_openai():
    req = TTSRequest(document_id=1)
    assert req.provider == "openai"


def test_provider_rejects_unknown_string():
    with pytest.raises(pydantic.ValidationError):
        TTSRequest(document_id=1, provider="whisper")


def test_provider_rejects_empty_string():
    with pytest.raises(pydantic.ValidationError):
        TTSRequest(document_id=1, provider="")


def test_provider_is_literal_type():
    """provider field annotation must be Literal, not plain str."""
    import typing
    field = TTSRequest.model_fields['provider']
    origin = getattr(field.annotation, '__origin__', None)
    assert origin is typing.Literal, (
        "TTSRequest.provider must be Literal['openai', 'elevenlabs'], not plain str"
    )