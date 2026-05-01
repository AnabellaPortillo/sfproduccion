from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .database import engine, Base
from .routers import auth, dashboard, patients, orders, results, equipment, catalog, statistics, admin

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LabCore LIS", version="1.0.0")

# Session middleware (secret key — change in production)
app.add_middleware(SessionMiddleware, secret_key="labcore-secret-key-2024-change-in-prod")

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(patients.router)
app.include_router(orders.router)
app.include_router(results.router)
app.include_router(equipment.router)
app.include_router(catalog.router)
app.include_router(statistics.router)
app.include_router(admin.router)
