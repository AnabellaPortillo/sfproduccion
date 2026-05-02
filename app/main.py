import json
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .database import engine, Base
from .routers import auth, dashboard, patients, orders, results, equipment, catalog, statistics, admin, imports
from .panels import migrate_columns, setup_panels

Base.metadata.create_all(bind=engine)
migrate_columns()
setup_panels()

app = FastAPI(title="LabCore LIS", version="1.0.0")

# SessionMiddleware debe ir primero (se agrega al final = se ejecuta primero en Starlette)
app.add_middleware(SessionMiddleware, secret_key="labcore-secret-key-2024-change-in-prod")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ── Jinja2 ────────────────────────────────────────────────────────────────────
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["tojson"] = lambda v: json.dumps(v, ensure_ascii=False)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(patients.router)
app.include_router(orders.router)
app.include_router(results.router)
app.include_router(equipment.router)
app.include_router(catalog.router)
app.include_router(statistics.router)
app.include_router(admin.router)
app.include_router(imports.router)
