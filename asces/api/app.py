from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from ..storage.db import Database
from ..storage.repo import AlertRepo
from ..config import load_config
import os

app = FastAPI(title="ASCeS API", version="0.1.0")

# Config & DB
config = load_config()
db = Database(config.db_path)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "../ui/static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory="asces/ui/templates")

# Dependency
def get_db():
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}

@app.get("/api/alerts")
def get_alerts(limit: int = 50, level: str = None, db_session: Session = Depends(get_db)):
    repo = AlertRepo(db_session)
    alerts = repo.get_alerts(limit=limit, level=level)
    return alerts

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db_session: Session = Depends(get_db)):
    repo = AlertRepo(db_session)
    alerts = repo.get_alerts(limit=100)
    return templates.TemplateResponse("index.html", {"request": request, "alerts": alerts})
