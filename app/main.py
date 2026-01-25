from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .db import Base, engine
from . import models  # noqa: F401

from .routes.clients import router as clients_router
from .routes.orders import router as orders_router
from .routes.payments import router as payments_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DesklyCRM")

app.include_router(clients_router)
app.include_router(orders_router)
app.include_router(payments_router)


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h1>DesklyCRM</h1>
    <p>Status: It works ✅</p>
    <p><a href="/health">Health check</a></p>
    <p><a href="/docs">API Docs</a></p>
    <p><a href="/docs#/clients/list_clients_api_clients_get">Clients (Swagger)</a></p>
    <p><a href="/docs#/orders/list_orders_api_orders_get">Orders (Swagger)</a></p>
    <p><a href="/docs#/payments">Payments (Swagger)</a></p>
    """


@app.get("/health")
def health():
    return {"status": "ok"}