from pydantic import BaseModel, Field


class TextRequest(BaseModel):
    """Request body for POST /summarize. Add more fields here for future features (e.g. style, length)."""
    text: str = Field(..., min_length=1)
