import asyncio
from sqlmodel import Session
from app.db import engine
from app.models.user import User
from app.models.document import Document

async def main():
    with Session(engine) as session:
        user = session.query(User).first()
        if not user:
            print("No user")
            user = User(email="test@example.com", hashed_password="pw")
            session.add(user)
            session.commit()
            session.refresh(user)
            
        doc = Document(
            user_id=user.id,
            url="pasted_text",
            title="Pasted Text",
            raw_content="This is a test document.",
            cleaned_content="This is a test document."
        )
        try:
            session.add(doc)
            session.commit()
            print("Document saved successfully! ID:", doc.id)
        except Exception as e:
            print("DB ERROR:", e)

asyncio.run(main())
