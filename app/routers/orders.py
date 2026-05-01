from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Order, OrderItem, OrderStatus, Urgency, Patient, Doctor, Test, TestCategory

router = APIRouter(prefix="/orders", tags=["orders"])
templates = Jinja2Templates(directory="app/templates")

PER_PAGE = 30


def _require_session(request: Request):
    if not request.session.get("user_id"):
        raise HTTPException(status_code=303, headers={"Location": "/auth/login"})


def _next_order_number(db: Session) -> str:
    today = datetime.now()
    prefix = today.strftime("%Y%m%d")
    last = (
        db.query(Order)
        .filter(Order.order_number.like(f"{prefix}%"))
        .order_by(Order.order_number.desc())
        .first()
    )
    if last:
        seq = int(last.order_number[-4:]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


@router.get("", response_class=HTMLResponse)
def list_orders(
    request: Request,
    q: str = "", status: str = "", urgency: str = "",
    date_from: str = "", date_to: str = "",
    page: int = 1,
    db: Session = Depends(get_db)
):
    _require_session(request)
    query = db.query(Order)
    if q:
        like = f"%{q}%"
        query = query.join(Patient).filter(
            Order.order_number.ilike(like) |
            Patient.last_name.ilike(like) |
            Patient.first_name.ilike(like) |
            Patient.document_number.ilike(like)
        )
    if status:
        query = query.filter(Order.status == status)
    if urgency:
        query = query.filter(Order.urgency == urgency)
    if date_from:
        query = query.filter(Order.order_date >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(Order.order_date <= datetime.fromisoformat(date_to + "T23:59:59"))

    total_count = query.count()
    orders = query.order_by(Order.order_date.desc()).offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()
    return templates.TemplateResponse("orders/list.html", {
        "request": request, "orders": orders, "total_count": total_count,
        "page": page, "per_page": PER_PAGE,
        "q": q, "status_filter": status, "urgency_filter": urgency,
        "date_from": date_from, "date_to": date_to,
        "active_page": "orders"
    })


@router.get("/new", response_class=HTMLResponse)
def new_order_form(request: Request, patient_id: Optional[int] = None, db: Session = Depends(get_db)):
    _require_session(request)
    patients = db.query(Patient).filter(Patient.is_active == True).order_by(Patient.last_name).all()
    doctors = db.query(Doctor).filter(Doctor.is_active == True).order_by(Doctor.last_name).all()
    categories = db.query(TestCategory).filter(TestCategory.is_active == True).all()
    selected_patient = db.query(Patient).filter(Patient.id == patient_id).first() if patient_id else None
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    return templates.TemplateResponse("orders/form.html", {
        "request": request, "patients": patients, "doctors": doctors,
        "categories": categories, "selected_patient": selected_patient,
        "now": now, "active_page": "new_order"
    })


@router.post("/new")
async def create_order(
    request: Request,
    patient_id: int = Form(...),
    doctor_id: str = Form(""),
    urgency: str = Form("ROUTINE"),
    order_date: str = Form(""),
    clinical_info: str = Form(""),
    observations: str = Form(""),
    db: Session = Depends(get_db)
):
    _require_session(request)
    form = await request.form()
    test_ids = form.getlist("test_ids")

    order = Order(
        order_number=_next_order_number(db),
        patient_id=patient_id,
        doctor_id=int(doctor_id) if doctor_id else None,
        urgency=Urgency(urgency),
        order_date=datetime.fromisoformat(order_date) if order_date else datetime.now(),
        clinical_info=clinical_info or None,
        observations=observations or None,
        created_by_id=request.session.get("user_id"),
    )
    db.add(order)
    db.flush()

    total = 0.0
    for tid in test_ids:
        test = db.query(Test).filter(Test.id == int(tid)).first()
        if test:
            item = OrderItem(order_id=order.id, test_id=test.id)
            db.add(item)
            total += test.price or 0.0

    order.total_price = total
    db.commit()
    return RedirectResponse(f"/orders/{order.id}", status_code=303)


@router.get("/{order_id}", response_class=HTMLResponse)
def order_detail(order_id: int, request: Request, db: Session = Depends(get_db)):
    _require_session(request)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404)
    return templates.TemplateResponse("orders/detail.html", {
        "request": request, "order": order, "active_page": "orders"
    })


@router.post("/{order_id}/status")
def update_order_status(
    order_id: int, request: Request,
    new_status: str = Form(...),
    db: Session = Depends(get_db)
):
    _require_session(request)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404)
    if new_status:
        order.status = OrderStatus(new_status)
        db.commit()
    return RedirectResponse(f"/orders/{order_id}", status_code=303)
