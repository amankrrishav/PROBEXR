from sqlmodel import Session, select
from app.models.document import Document
from app.models.synthesis import Synthesis
from app.services.llm import chat_completion

async def synthesize_documents(document_ids: list[int], user_id: int, session: Session, prompt: str | None = None) -> Synthesis:
    statement = select(Document).where(Document.id.in_(document_ids), Document.user_id == user_id) # type: ignore
    docs = session.exec(statement).all()
    
    if len(docs) != len(document_ids):
        raise ValueError("One or more documents not found or unauthorized")
        
    if len(docs) < 2:
        raise ValueError("At least two documents needed for synthesis")

    combined_text = "\n\n".join([f"--- Document {i+1}: {d.title} ---\n{d.cleaned_content[:4000]}" for i, d in enumerate(docs)])
    
    system_prompt = "You are an expert analyst. Synthesize the following documents, extracting common themes, contrasting viewpoints, and providing a comprehensive overview."
    if prompt:
        system_prompt += f"\n\nAdditional instructions from user: {prompt}"
        
    user_prompt = f"Documents:\n\n{combined_text}\n\nPlease synthesize these documents."
    
    summary = await chat_completion(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1500,
        temperature=0.3
    )

    synthesis_record = Synthesis(
        user_id=user_id,
        summary=summary,
        documents=docs
    )
    session.add(synthesis_record)
    session.commit()
    session.refresh(synthesis_record)
    
    return synthesis_record
