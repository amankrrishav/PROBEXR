from pydantic import BaseModel, Field


class TextRequest(BaseModel):
    """Request body for POST /summarize. Add more fields here for future features (e.g. style, length)."""
    text: str = Field(..., min_length=1, max_length=100_000, description="Max 100k chars to prevent DoS")

class URLRequest(BaseModel):
    url: str = Field(..., description="URL to scrape and ingest")

class SynthesisRequest(BaseModel):
    document_ids: list[int] = Field(..., min_length=2, description="List of at least two Document IDs to synthesize")
    prompt: str | None = Field(default=None, description="Optional custom prompt for synthesis")

class ChatRequest(BaseModel):
    document_id: int = Field(..., description="ID of the document to chat about")
    message: str = Field(..., description="User message to the assistant")
    session_id: int | None = Field(default=None, description="Provide an existing session ID to continue a chat")

class FlashcardRequest(BaseModel):
    document_id: int = Field(..., description="ID of the document to generate flashcards from")
    count: int = Field(default=10, le=50, description="Desired number of flashcards")

class TTSRequest(BaseModel):
    document_id: int = Field(..., description="ID of the document to narrate")
    provider: str = Field(default="openai", description="TTS provider, e.g. 'openai' or 'elevenlabs'")
