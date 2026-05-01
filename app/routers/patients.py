from datetime import date
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Patient, Gender

router = APIRouter(prefix="/patients", tags=["patients"])
templates = Jinja2Templates(directory="app/templates")

PER_PAGE = 30


def _require_session(request: Request):
    if not request.session.get("user_id"):
        raise HTTPException(status_code=303, headers={"Location": "/auth/login"})


@router.get("", response_class=HTMLResponse)
def list_patients(request: Request, q: str = "", page: int = 1, db: Session = Depends(get_db)):
    _require_session(request)
    query = db.query(Patient).filter(Patient.is_active == True)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Patient.last_name.ilike(like)) |
            (Patient.first_name.ilike(like)) |
            (Patient.document_number.ilike(like))
        )
    total = query.count()
    patients = query.order_by(Patient.last_name).offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()
    return templates.TemplateResponse("patients/list.html", {
        "request": request, "patients": patients, "total": total,
        "page": page, "per_page": PER_PAGE, "search_q": q,
        "active_page": "patients"
    })


@router.get("/new", response_class=HTMLResponse)
def new_patient_form(request: Request):
    _require_session(request)
    return templates.TemplateResponse("patients/form.html", {"request": request, "patient": None, "active_page": "patients"})


@router.post("/new")
async def create_patient(
    request: Request,
    document_type: str = Form("DNI"),
    document_number: str = Form(...),
    last_name: str = Form(...),
    first_name: str = Form(...),
    birth_date: str = Form(...),
    gender: str = Form(...),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    city: str = Form(""),
    health_insurance: str = Form(""),
    insurance_number: str = Form(""),
    observations: str = Form(""),
    db: Session = Depends(get_db)
):
    _require_session(request)
    patient = Patient(
        document_type=document_type,
        document_number=document_number,
        last_name=last_name.strip().upper(),
        first_name=first_name.strip(),
        birth_date=date.fromisoformat(birth_date),
        gender=Gender(gender),
        phone=phone or None,
        email=email or None,
        address=address or None,
        city=city or None,
        health_insurance=health_insurance or None,
        insurance_number=insurance_number or None,
        observations=observations or None,
    )
    db.add(patient)
    db.commit()
    return RedirectResponse(f"/patients/{patient.id}", status_code=303)


@router.get("/{patient_id}", response_class=HTMLResponse)
def patient_detail(patient_id: int, request: Request, db: Session = Depends(get_db)):
    _require_session(request)
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(404, "Paciente no encontrado")
    today = date.today()
    age = today.year - patient.birth_date.year - (
        (today.month, today.day) < (patient.birth_date.month, patient.birth_date.day)
    )
    return templates.TemplateResponse("patients/detail.html", {
        "request": request, "patient": patient, "age": age, "active_page": "patients"
    })


@router.get("/{patient_id}/edit", response_class=HTMLResponse)
def edit_patient_form(patient_id: int, request: Request, db: Session = Depends(get_db)):
    _require_session(request)
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(404)
    return templates.TemplateResponse("patients/form.html", {"request": request, "patient": patient, "active_page": "patients"})


@router.post("/{patient_id}/edit")
async def update_patient(
    patient_id: int, request: Request,
    document_type: str = Form("DNI"),
    document_number: str = Form(...),
    last_name: str = Form(...),
    first_name: str = Form(...),
    birth_date: str = Form(...),
    gender: str = Form(...),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    city: str = Form(""),
    health_insurance: str = Form(""),
    insurance_number: str = Form(""),
    observations: str = Form(""),
    db: Session = Depends(get_db)
):
    _require_session(request)
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(404)
    patient.document_type = document_type
    patient.document_number = document_number
    patient.last_name = last_name.strip().upper()
    patient.first_name = first_name.strip()
    patient.birth_date = date.fromisoformat(birth_date)
    patient.gender = Gender(gender)
    patient.phone = phone or None
    patient.email = email or None
    patient.address = address or None
    patient.city = city or None
    patient.health_insurance = health_insurance or None
    patient.insurance_number = insurance_number or None
    patient.observations = observations or None
    db.commit()
    return RedirectResponse(f"/patients/{patient_id}", status_code=303)
