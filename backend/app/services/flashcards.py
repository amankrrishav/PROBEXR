import json
from sqlmodel import Session
from app.models.document import Document
from app.models.flashcards import FlashcardSet, Flashcard
from app.services.llm import chat_completion
import csv
from io import StringIO

async def generate_flashcards(document_id: int, user_id: int, session: Session, count: int = 10) -> FlashcardSet:
    doc = session.get(Document, document_id)
    if not doc or doc.user_id != user_id:
        raise ValueError("Document not found or unauthorized")
        
    system_prompt = (
        f"You are a studying assistant. Create exactly {count} flashcards from the provided document. "
        "Return the flashcards strictly as a JSON list of objects, where each object has 'front' and 'back' keys. "
        "Do not include any other text or markdown wrapping outside of the JSON array."
    )
    user_prompt = f"Document Title: {doc.title}\n\nDocument Content:\n{doc.cleaned_content[:8000]}"
    
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
    session.commit()
    session.refresh(fc_set)
    
    # Create Cards
    for card in flashcards_data:
        if "front" in card and "back" in card:
            fc = Flashcard(set_id=fc_set.id, front=card["front"], back=card["back"])
            session.add(fc)
            
    session.commit()
    session.refresh(fc_set)
    return fc_set

def generate_csv_export(flashcards: list[Flashcard]) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Front", "Back"])
    for fc in flashcards:
        writer.writerow([fc.front, fc.back])
    return output.getvalue()
