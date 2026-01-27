from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import os
import time
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse, Response, RedirectResponse
from sqlalchemy import text
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from .db import init_db, make_engine, make_sessionmaker, run_migrations
from . import models  # noqa: F401

from .routes.clients import router as clients_router
from .routes.orders import router as orders_router
from .routes.payments import router as payments_router
from .routes.export import router as export_router
from .routes.ui import router as ui_router
from .routes.auth import router as auth_router
from .routes.activity import router as activity_router
from .routes.reminders import router as reminders_router
from .auth import PUBLIC_PATHS, get_current_user, has_users


REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration seconds",
    ["method", "path"],
)


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
    app.state.start_time = time.time()

    @app.middleware("http")
    async def auth_middleware(request, call_next):
        path = request.url.path
        if path.startswith("/static") or path in PUBLIC_PATHS or path.startswith("/redoc"):
            request.state.user = None
            return await call_next(request)

        db = SessionLocal()
        try:
            if not has_users(db):
                if path.startswith("/ui"):
                    return RedirectResponse(url="/setup", status_code=303)
                if path.startswith("/api"):
                    return JSONResponse({"detail": "setup required"}, status_code=503)
                request.state.user = None
                return await call_next(request)

            try:
                user = get_current_user(request, db)
            except HTTPException as exc:
                if path.startswith("/ui"):
                    return RedirectResponse(url="/login", status_code=303)
                return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
            request.state.user = user
            if request.method in {"POST", "PUT", "PATCH", "DELETE"} and user.role == "viewer":
                if path.startswith("/ui"):
                    return HTMLResponse("Forbidden", status_code=403)
                return JSONResponse({"detail": "forbidden"}, status_code=403)
            return await call_next(request)
        finally:
            db.close()

    @app.middleware("http")
    async def log_requests(request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            route = request.scope.get("route")
            path = getattr(route, "path", request.url.path)
            REQUEST_COUNT.labels(request.method, path, "500").inc()
            REQUEST_LATENCY.labels(request.method, path).observe(duration_ms / 1000)
            logger.exception(
                "request failed method=%s path=%s id=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                request_id,
                duration_ms,
            )
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
        REQUEST_LATENCY.labels(request.method, path).observe(duration_ms / 1000)
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
    app.include_router(auth_router)
    app.include_router(clients_router)
    app.include_router(orders_router)
    app.include_router(payments_router)
    app.include_router(export_router)
    app.include_router(activity_router)
    app.include_router(reminders_router)

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
        service = "deskly-crm"
        version = os.getenv("APP_VERSION", "0.0.0")
        uptime_seconds = max(0, time.time() - app.state.start_time)
        db_status = "ok"
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception:
            db_status = "error"

        payload = {
            "status": "ok" if db_status == "ok" else "error",
            "service": service,
            "version": version,
            "db": db_status,
            "uptime_seconds": round(uptime_seconds, 2),
        }
        if db_status != "ok":
            return JSONResponse(status_code=503, content=payload)
        return payload

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app
