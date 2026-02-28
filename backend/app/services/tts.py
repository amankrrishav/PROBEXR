"""
TTS service.

CURRENT STATE: STUB / DEMO MODE
---------------------------------
The actual TTS pipeline is not yet implemented.  This service currently:
  1. Validates doc ownership (user isolation is enforced).
  2. Validates the requested provider against an allowed list (prevents open-ended
     string injection into future provider dispatch logic).
  3. Returns a FAKE audio URL for UI development purposes — no real audio is generated.

PRODUCTION IMPLEMENTATION (next milestone):
  1. Use the summarizer service to generate a concise text summary of the document.
  2. Send that summary text to the selected provider's TTS API:
       - OpenAI  : POST https://api.openai.com/v1/audio/speech
       - ElevenLabs: POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
  3. Stream the returned audio bytes directly to the client (StreamingResponse) or
     upload to S3-compatible storage and save the public URL in AudioSummary.audio_url.
  4. Clean up any temp files after the response is sent.
  5. Enforce a text-length cap before the TTS call (e.g. 4 000 chars) to bound cost/latency.

Because this is a stub, the TTS button in the UI will show "Audio Ready" but the link
will not resolve to a real audio file until the above is implemented.
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.tts import AudioSummary

_ALLOWED_PROVIDERS = {"openai", "elevenlabs"}


async def generate_audio_summary(
    document_id: int,
    user_id: int,
    provider: str,
    session: AsyncSession,
) -> AudioSummary:
    # 1. Validate provider against allowed list
    if provider not in _ALLOWED_PROVIDERS:
        raise ValueError(
            f"Unsupported TTS provider '{provider}'. "
            f"Allowed: {', '.join(sorted(_ALLOWED_PROVIDERS))}"
        )

    # 2. Ownership check
    doc = await session.get(Document, document_id)
    if not doc or doc.user_id != user_id:
        raise ValueError("Document not found or unauthorized")

    # 3. STUB: simulate a successful TTS response
    # Replace this block with real provider calls in the production milestone.
    fake_url = f"https://storage.readpulse.local/audio/{uuid.uuid4()}.mp3"

    audio_record = AudioSummary(
        user_id=user_id,
        document_id=document_id,
        audio_url=fake_url,
        provider=provider,
    )
    session.add(audio_record)
    await session.commit()
    await session.refresh(audio_record)
    return audio_record
