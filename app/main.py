import json
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .database import engine, Base
from .routers import auth, dashboard, patients, orders, results, equipment, catalog, statistics, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LabCore LIS", version="1.0.0")

app.add_middleware(SessionMiddleware, secret_key="labcore-secret-key-2024-change-in-prod")


class FlashMiddleware(BaseHTTPMiddleware):
    """Extracts flash messages from session before each request."""
    async def dispatch(self, request: Request, call_next):
        request.state.flash_messages = request.session.pop("_flash", [])
        return await call_next(request)


app.add_middleware(FlashMiddleware)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ── Jinja2 global config ──────────────────────────────────────────────────────
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["tojson"] = lambda v: json.dumps(v, ensure_ascii=False)
templates.env.globals["flash_messages"] = []

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(patients.router)
app.include_router(orders.router)
app.include_router(results.router)
app.include_router(equipment.router)
app.include_router(catalog.router)
app.include_router(statistics.router)
app.include_router(admin.router)
