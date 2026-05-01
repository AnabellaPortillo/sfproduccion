from datetime import date
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Equipment, EquipmentStatus

router = APIRouter(prefix="/equipment", tags=["equipment"])
templates = Jinja2Templates(directory="app/templates")


def _require_session(request: Request):
    if not request.session.get("user_id"):
        raise HTTPException(status_code=303, headers={"Location": "/auth/login"})


@router.get("", response_class=HTMLResponse)
def list_equipment(request: Request, db: Session = Depends(get_db)):
    _require_session(request)
    equipment = db.query(Equipment).order_by(Equipment.name).all()
    today = date.today().isoformat()
    return templates.TemplateResponse("equipment/list.html", {
        "request": request, "equipment": equipment, "today": today, "active_page": "equipment"
    })


@router.get("/new", response_class=HTMLResponse)
def new_equipment_form(request: Request):
    _require_session(request)
    return templates.TemplateResponse("equipment/form.html", {"request": request, "eq": None, "active_page": "equipment"})


@router.post("/new")
async def create_equipment(
    request: Request,
    name: str = Form(...),
    manufacturer: str = Form(""),
    model: str = Form(""),
    serial_number: str = Form(""),
    equipment_type: str = Form(""),
    location: str = Form(""),
    status: str = Form("ACTIVE"),
    last_calibration: str = Form(""),
    next_calibration: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    _require_session(request)
    eq = Equipment(
        name=name,
        manufacturer=manufacturer or None,
        model=model or None,
        serial_number=serial_number or None,
        equipment_type=equipment_type or None,
        location=location or None,
        status=EquipmentStatus(status),
        last_calibration=date.fromisoformat(last_calibration) if last_calibration else None,
        next_calibration=date.fromisoformat(next_calibration) if next_calibration else None,
        notes=notes or None,
    )
    db.add(eq)
    db.commit()
    return RedirectResponse("/equipment", status_code=303)


@router.get("/{eq_id}/edit", response_class=HTMLResponse)
def edit_equipment_form(eq_id: int, request: Request, db: Session = Depends(get_db)):
    _require_session(request)
    eq = db.query(Equipment).filter(Equipment.id == eq_id).first()
    if not eq:
        raise HTTPException(404)
    return templates.TemplateResponse("equipment/form.html", {"request": request, "eq": eq, "active_page": "equipment"})


@router.post("/{eq_id}/edit")
async def update_equipment(
    eq_id: int,
    request: Request,
    name: str = Form(...),
    manufacturer: str = Form(""),
    model: str = Form(""),
    serial_number: str = Form(""),
    equipment_type: str = Form(""),
    location: str = Form(""),
    status: str = Form("ACTIVE"),
    last_calibration: str = Form(""),
    next_calibration: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    _require_session(request)
    eq = db.query(Equipment).filter(Equipment.id == eq_id).first()
    if not eq:
        raise HTTPException(404)
    eq.name = name
    eq.manufacturer = manufacturer or None
    eq.model = model or None
    eq.serial_number = serial_number or None
    eq.equipment_type = equipment_type or None
    eq.location = location or None
    eq.status = EquipmentStatus(status)
    eq.last_calibration = date.fromisoformat(last_calibration) if last_calibration else None
    eq.next_calibration = date.fromisoformat(next_calibration) if next_calibration else None
    eq.notes = notes or None
    db.commit()
    return RedirectResponse("/equipment", status_code=303)
