from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TextRequest(BaseModel):
    """Request body for POST /summarize and POST /summarize/stream."""
    text: str = Field(..., min_length=1, max_length=100_000, description="Max 100k chars to prevent DoS")
    length: Literal["brief", "standard", "detailed"] = Field(default="standard", description="Summary length: brief, standard, or detailed")
    mode: Literal["paragraph", "bullets", "key_sentences", "abstract", "tldr", "outline", "executive"] = Field(
        default="paragraph", description="Summary output format"
    )
    tone: Literal["neutral", "formal", "casual", "creative", "technical"] = Field(
        default="neutral", description="Writing tone/style"
    )
    keywords: list[str] = Field(default_factory=list, max_length=5, description="Up to 5 focus keywords to emphasize")

class URLRequest(BaseModel):
    url: str = Field(..., max_length=2048, description="URL to scrape and ingest")

    @field_validator("url")
    @classmethod
    def validate_url_scheme(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

class TextIngestRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500_000, description="Text to save as a Document (max 500k chars)")
    title: str = Field(default="Pasted Text", max_length=200, description="Optional title")

class SynthesisRequest(BaseModel):
    document_ids: list[int] = Field(..., min_length=2, max_length=10, description="List of at least two Document IDs to synthesize")
    prompt: str | None = Field(default=None, max_length=500, description="Optional custom prompt for synthesis")

class ChatRequest(BaseModel):
    document_id: int = Field(..., description="ID of the document to chat about")
    message: str = Field(..., max_length=2000, description="User message to the assistant")
    session_id: int | None = Field(default=None, description="Provide an existing session ID to continue a chat")

class FlashcardRequest(BaseModel):
    document_id: int = Field(..., description="ID of the document to generate flashcards from")
    count: int = Field(default=10, ge=1, le=50, description="Desired number of flashcards (1-50)")

class TTSRequest(BaseModel):
    document_id: int = Field(..., description="ID of the document to narrate")
    provider: Literal["openai", "elevenlabs"] = Field(default="openai", description="TTS provider")