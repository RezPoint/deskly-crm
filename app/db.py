import os
from typing import Generator, Optional

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()

DEFAULT_DB_URL = os.getenv("DATABASE_URL", "sqlite:///./desklycrm.db")


def make_engine(database_url: Optional[str] = None):
    url = database_url or DEFAULT_DB_URL
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, future=True)


def make_sessionmaker(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


# дефолтные engine/SessionLocal -- для обычного запуска
engine = make_engine()
SessionLocal = make_sessionmaker(engine)


def init_db(bind_engine=None) -> None:
    auto_create = os.getenv("AUTO_CREATE_DB", "1") == "1"
    if auto_create:
        Base.metadata.create_all(bind=bind_engine or engine)


def get_db(request: Request) -> Generator[Session, None, None]:
    """
    Берём SessionLocal из app.state (если app создан через create_app),
    иначе используем дефолтный SessionLocal.
    """
    session_factory = getattr(request.app.state, "SessionLocal", SessionLocal)

    db = session_factory()
    try:
        yield db
    finally:
        db.close()
