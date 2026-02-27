from sqlmodel import SQLModel, create_engine, Session

from app.config import get_config

DATABASE_URL = get_config().database_url

engine = create_engine(DATABASE_URL, echo=False)

from typing import Generator

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session