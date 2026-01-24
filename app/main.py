from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="DesklyCRM")

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h1>DesklyCRM</h1>
    <p>Status: It works ✅</p>
    <p><a href="/health">Health check</a></p>
    """
    
@app.get("/health")
def health():
    return {"status": "ok"}