import json
import csv
from io import StringIO

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.document import Document
from app.models.flashcards import FlashcardSet, Flashcard
from app.services.llm import chat_completion
from app.services.prompt_sanitizer import sanitize_document_content


async def generate_flashcards(document_id: int, user_id: int, session: AsyncSession, count: int = 10) -> FlashcardSet:
    doc = await session.get(Document, document_id)
    if not doc or doc.user_id != user_id:
        raise ValueError("Document not found or unauthorized")
        
    system_prompt = (
        f"You are a studying assistant. Create exactly {count} flashcards from the provided document. "
        "Return the flashcards strictly as a JSON list of objects, where each object has 'front' and 'back' keys. "
        "Do not include any other text or markdown wrapping outside of the JSON array."
    )
    # Sanitize document content before injecting into the prompt
    safe_title = sanitize_document_content(doc.title or "")
    safe_content = sanitize_document_content((doc.cleaned_content or "")[:8000])
    user_prompt = f"Document Title: {safe_title}\n\nDocument Content:\n{safe_content}"
    
    reply = await chat_completion(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=2000,
        temperature=0.3
    )
    
    try:
        # Simple extraction in case LLM wraps the json in markdown block
        json_str = reply.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
            
        flashcards_data = json.loads(json_str.strip())
    except json.JSONDecodeError:
        raise ValueError("Failed to parse LLM flashcards output as JSON")
        
    # Create Set
    fc_set = FlashcardSet(user_id=user_id, document_id=document_id)
    session.add(fc_set)
    await session.commit()
    await session.refresh(fc_set)
    
    # Create Cards
    for card in flashcards_data:
        if "front" in card and "back" in card:
            fc = Flashcard(set_id=fc_set.id, front=card["front"], back=card["back"])
            session.add(fc)
            
    await session.commit()
    await session.refresh(fc_set)
    return fc_set

def generate_csv_export(flashcards: list[Flashcard]) -> str:
    """
    Produce an Anki-compatible CSV.

    Anki CSV format rules:
      - No header row (Anki expects data-only).
      - Two columns: Front, Back.
      - Fields must not contain raw newlines or tabs (they break the TSV-style parser).
        We replace them with a space before writing.
    """
    output = StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    for fc in flashcards:
        front = fc.front.replace("\n", " ").replace("\t", " ").strip()
        back = fc.back.replace("\n", " ").replace("\t", " ").strip()
        writer.writerow([front, back])
    return output.getvalue()


async def export_flashcards(session: AsyncSession, set_id: int, user_id: int) -> str:
    fc_set = await session.get(FlashcardSet, set_id)
    if not fc_set or fc_set.user_id != user_id:
        raise ValueError("Flashcard set not found or unauthorized")
        
    result = await session.execute(
        select(Flashcard).where(Flashcard.set_id == set_id)
    )
    flashcards = list(result.scalars().all())
    
    return generate_csv_export(flashcards)