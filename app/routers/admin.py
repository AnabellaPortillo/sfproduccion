from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, UserRole, Doctor

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _require_admin(request: Request):
    role = request.session.get("role")
    if role not in ["ADMIN", "SUPERVISOR"]:
        raise HTTPException(403, "Acceso denegado")


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
def list_users(request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    users = db.query(User).order_by(User.full_name).all()
    return templates.TemplateResponse("admin/users.html", {
        "request": request, "users": users, "active_page": "users"
    })


@router.get("/users/new", response_class=HTMLResponse)
def new_user_form(request: Request):
    _require_admin(request)
    return templates.TemplateResponse("admin/user_form.html", {
        "request": request, "user": None, "roles": UserRole, "active_page": "users"
    })


@router.post("/users/new")
async def create_user(
    request: Request,
    username: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(""),
    password: str = Form(...),
    role: str = Form("TECHNICIAN"),
    db: Session = Depends(get_db)
):
    _require_admin(request)
    user = User(
        username=username,
        full_name=full_name,
        email=email or None,
        hashed_password=pwd_context.hash(password),
        role=UserRole(role),
    )
    db.add(user)
    db.commit()
    return RedirectResponse("/admin/users", status_code=303)


# ── Doctors ───────────────────────────────────────────────────────────────────

@router.get("/doctors", response_class=HTMLResponse)
def list_doctors(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        raise HTTPException(303, headers={"Location": "/auth/login"})
    doctors = db.query(Doctor).order_by(Doctor.last_name).all()
    return templates.TemplateResponse("admin/doctors.html", {
        "request": request, "doctors": doctors, "active_page": "doctors"
    })


@router.get("/doctors/new", response_class=HTMLResponse)
def new_doctor_form(request: Request):
    if not request.session.get("user_id"):
        raise HTTPException(303, headers={"Location": "/auth/login"})
    return templates.TemplateResponse("admin/doctor_form.html", {
        "request": request, "doctor": None, "active_page": "doctors"
    })


@router.post("/doctors/new")
async def create_doctor(
    request: Request,
    last_name: str = Form(...),
    first_name: str = Form(...),
    specialty: str = Form(""),
    license_number: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    db: Session = Depends(get_db)
):
    if not request.session.get("user_id"):
        return RedirectResponse("/auth/login", status_code=303)
    doctor = Doctor(
        last_name=last_name.strip().upper(),
        first_name=first_name.strip(),
        specialty=specialty or None,
        license_number=license_number or None,
        phone=phone or None,
        email=email or None,
    )
    db.add(doctor)
    db.commit()
    return RedirectResponse("/admin/doctors", status_code=303)


@router.get("/doctors/{doctor_id}/edit", response_class=HTMLResponse)
def edit_doctor_form(doctor_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/auth/login", status_code=303)
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(404)
    return templates.TemplateResponse("admin/doctor_form.html", {
        "request": request, "doctor": doctor, "active_page": "doctors"
    })


@router.post("/doctors/{doctor_id}/edit")
async def update_doctor(
    doctor_id: int, request: Request,
    last_name: str = Form(...),
    first_name: str = Form(...),
    specialty: str = Form(""),
    license_number: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(404)
    doctor.last_name = last_name.strip().upper()
    doctor.first_name = first_name.strip()
    doctor.specialty = specialty or None
    doctor.license_number = license_number or None
    doctor.phone = phone or None
    doctor.email = email or None
    db.commit()
    return RedirectResponse("/admin/doctors", status_code=303)
