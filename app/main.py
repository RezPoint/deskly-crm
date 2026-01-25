from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .db import init_db, make_engine, make_sessionmaker
from . import models  # noqa: F401

from .routes.clients import router as clients_router
from .routes.orders import router as orders_router
from .routes.payments import router as payments_router
from .routes.export import router as export_router
from .routes.ui import router as ui_router


def create_app(database_url: str | None = None) -> FastAPI:
    app = FastAPI(title="DesklyCRM")

    engine = make_engine(database_url)
    app.state.engine = engine
    app.state.SessionLocal = make_sessionmaker(engine)

    @app.on_event("startup")
    def _startup():
        init_db(engine)

    app.include_router(clients_router)
    app.include_router(orders_router)
    app.include_router(payments_router)
    app.include_router(export_router)
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

  <p><a href="/health">Health check</a></p>
  <p><a href="/docs">API Docs</a></p>

  <p><a href="/docs#/clients/list_clients_api_clients_get">Clients (Swagger)</a></p>
  <p><a href="/docs#/orders/list_orders_api_orders_get">Orders (Swagger)</a></p>
  <p><a href="/docs#/payments/create_payment_api_payments_post">Payments (Swagger)</a></p>
  <p><a href="/docs#/export/export_orders_csv_api_export_orders_csv_get">Export Orders CSV</a></p>
  <p><a href="/docs#/export/export_clients_csv_api_export_clients_csv_get">Export Clients CSV</a></p>
</body>
</html>
"""

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()