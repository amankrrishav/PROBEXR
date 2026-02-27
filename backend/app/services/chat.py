from sqlmodel import Session, select
from app.models.document import Document
from app.models.chat import ChatSession, ChatMessage
from app.services.llm import chat_completion

async def process_chat_message(document_id: int, user_id: int, message: str, session: Session, session_id: int | None = None) -> ChatMessage:
    # 1. Ensure user owns document
    doc = session.get(Document, document_id)
    if not doc or doc.user_id != user_id:
        raise ValueError("Document not found or unauthorized")
        
    # 2. Get or create session
    if session_id:
        chat_session = session.get(ChatSession, session_id)
        if not chat_session or chat_session.user_id != user_id or chat_session.document_id != document_id:
            raise ValueError("Chat session not found or mismatched")
    else:
        chat_session = ChatSession(user_id=user_id, document_id=document_id)
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        session_id = chat_session.id
        
    # 3. Save user message
    user_msg = ChatMessage(session_id=session_id, role="user", content=message)
    session.add(user_msg)
    session.commit()
    
    # 4. Fetch recent messages for context (token truncation alternative: just take last 10 messages)
    history_stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.desc()).limit(10) # type: ignore
    recent_msgs = session.exec(history_stmt).all()
    recent_msgs_list = list(recent_msgs)
    recent_msgs_list.reverse() # chronological order
    
    # 5. Prepare LLM prompt
    messages_payload: list[dict[str, str]] = [
        {"role": "system", "content": f"You are a helpful assistant answering questions about the following document:\n\nTitle: {doc.title}\n\nContent:\n{doc.cleaned_content[:5000]}"}
    ]
    for m in recent_msgs_list:
        messages_payload.append({"role": m.role, "content": m.content})
        
    # 6. Get response
    reply_content = await chat_completion(messages_payload, max_tokens=1000, temperature=0.5)
    
    # 7. Save assistant message
    assistant_msg = ChatMessage(session_id=session_id, role="assistant", content=reply_content)
    session.add(assistant_msg)
    session.commit()
    session.refresh(assistant_msg)
    
    return assistant_msg
