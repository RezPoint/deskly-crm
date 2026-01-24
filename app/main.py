from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .db import Base, engine
from . import models  # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DesklyCRM")
from .routes.clients import router as clients_router
app.include_router(clients_router)

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h1>DesklyCRM</h1>
    <p>Status: It works ✅</p>
    <p><a href="/health">Health check</a></p>
    <p><a href="/docs">API Docs</a></p>
    """
    
@app.get("/health")
def health():
    return {"status": "ok"}