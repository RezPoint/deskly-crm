from typing import Generator
from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from .config import settings

def make_engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)

engine = make_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

Base = declarative_base()

def get_db(request: Request) -> Generator[Session, None, None]:
    """Dependency injection to get DB session per request"""
    session_factory = getattr(request.app.state, "SessionLocal", SessionLocal)
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
