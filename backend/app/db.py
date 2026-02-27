from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./readpulse.db"

engine = create_engine(DATABASE_URL, echo=False)

from typing import Generator

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session