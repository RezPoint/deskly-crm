from contextlib import asynccontextmanager
import logging
import os
import time
import uuid

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .core.config import settings
from .core.database import Base, engine, SessionLocal, get_db
from .api.v1.router import api_router
from .core.security import get_current_user

# Создаем модели, если задано в конфигурации
if settings.AUTO_CREATE_DB:
    Base.metadata.create_all(bind=engine)

def _configure_logging() -> None:
    level = settings.LOG_LEVEL.upper()
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    logging.getLogger("desklycrm").setLevel(level)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = engine
    app.state.SessionLocal = SessionLocal
    # Здесь можно добавить запуск миграций при старте (MIGRATE_ON_START)
    yield
    # Очистка при завершении работы
    engine.dispose()

def create_app() -> FastAPI:
    _configure_logging()
    
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.APP_VERSION, lifespan=lifespan)
    logger = logging.getLogger("desklycrm")
    app.state.start_time = time.time()

    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Раздача статических файлов для Frontend SPA
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app

app = create_app()
