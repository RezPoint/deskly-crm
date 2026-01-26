from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import os
import time
import uuid
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .db import init_db, make_engine, make_sessionmaker, run_migrations
from . import models  # noqa: F401

from .routes.clients import router as clients_router
from .routes.orders import router as orders_router
from .routes.payments import router as payments_router
from .routes.export import router as export_router
from .routes.ui import router as ui_router


def _configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    logging.getLogger("desklycrm").setLevel(level)


def create_app(database_url: Optional[str] = None) -> FastAPI:
    _configure_logging()
    engine = make_engine(database_url)
    SessionLocal = make_sessionmaker(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = engine
        app.state.SessionLocal = SessionLocal
        if os.getenv("MIGRATE_ON_START", "0") == "1":
            run_migrations(database_url)
        else:
            init_db(engine)
        yield

    app = FastAPI(title="DesklyCRM", lifespan=lifespan)
    logger = logging.getLogger("desklycrm")

    @app.middleware("http")
    async def log_requests(request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request failed method=%s path=%s id=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                request_id,
                duration_ms,
            )
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request method=%s path=%s status=%s duration_ms=%.2f id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response

    # API
    app.include_router(clients_router)
    app.include_router(orders_router)
    app.include_router(payments_router)
    app.include_router(export_router)

    # UI
    app.include_router(ui_router)

    @app.get("/", response_class=HTMLResponse)
    def home():
        return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>DesklyCRM</title>
</head>
<body>
  <h1>DesklyCRM</h1>
  <p>Status: It works &#x2705;</p>

  <h3>UI</h3>
  <ul>
    <li><a href="/ui/clients">Clients</a></li>
    <li><a href="/ui/orders">Orders</a></li>
  </ul>

  <h3>API</h3>
  <ul>
    <li><a href="/health">Health</a></li>
    <li><a href="/docs">Swagger</a></li>
  </ul>
</body>
</html>
"""

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "deskly-crm"}

    return app
