from __future__ import annotations

from contextlib import asynccontextmanager
import os
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


def create_app(database_url: Optional[str] = None) -> FastAPI:
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
        return {"status": "ok"}

    return app
