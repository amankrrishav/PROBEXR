import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.document import Document
from app.models.synthesis import Synthesis
from app.services.llm import chat_completion
from app.services.prompt_sanitizer import sanitize_document_content, sanitize_user_prompt

logger = logging.getLogger(__name__)

# Global cap for the combined document content sent to the LLM.
# 16 000 chars ≈ 4 000 tokens — safe for 8K-context models after
# accounting for system prompt, user prompt wrapper, and response tokens.
COMBINED_CONTENT_CAP = 16_000

async def synthesize_documents(document_ids: list[int], user_id: int, session: AsyncSession, prompt: str | None = None) -> Synthesis:
    statement = select(Document).where(Document.id.in_(document_ids), Document.user_id == user_id)  # type: ignore
    result = await session.execute(statement)
    docs = list(result.scalars().all())
    
    if len(docs) != len(document_ids):
        raise ValueError("One or more documents not found or unauthorized")
        
    if len(docs) < 2:
        raise ValueError("At least two documents needed for synthesis")

    # Distribute the global cap evenly across documents
    per_doc_cap = COMBINED_CONTENT_CAP // len(docs)

    parts: list[str] = []
    for i, d in enumerate(docs):
        content = d.cleaned_content or ""
        if len(content) > per_doc_cap:
            logger.warning(
                "Synthesis: document %d ('%s') truncated from %d to %d chars",
                d.id, d.title, len(content), per_doc_cap,
            )
            content = content[:per_doc_cap]
        # Sanitize document content and title before injecting into prompt
        safe_content = sanitize_document_content(content)
        safe_title = sanitize_document_content(d.title or "")
        parts.append(f"--- Document {i+1}: {safe_title} ---\n{safe_content}")

    combined_text = "\n\n".join(parts)

    system_prompt = "You are an expert analyst. Synthesize the following documents, extracting common themes, contrasting viewpoints, and providing a comprehensive overview."
    if prompt:
        # Sanitize the user-supplied synthesis instruction before injecting
        safe_prompt = sanitize_user_prompt(prompt)
        system_prompt += f"\n\nAdditional instructions from user: {safe_prompt}"
        
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
    await session.commit()
    await session.refresh(synthesis_record)
    
    return synthesis_record