from datetime import datetime
from itertools import groupby
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Order, OrderItem, OrderItemStatus, Result, ResultStatus,
    Equipment, TestCategory
)

router = APIRouter(prefix="/results", tags=["results"])
templates = Jinja2Templates(directory="app/templates")

PER_PAGE = 50


def _require_session(request: Request):
    if not request.session.get("user_id"):
        raise HTTPException(status_code=303, headers={"Location": "/auth/login"})


def _compute_flag(value: str, ref_min, ref_max) -> tuple[bool, str]:
    try:
        v = float(value.replace(",", "."))
        if ref_max is not None and v > ref_max:
            return True, "H"
        if ref_min is not None and v < ref_min:
            return True, "L"
    except (ValueError, TypeError):
        pass
    return False, ""


@router.get("", response_class=HTMLResponse)
def list_results(
    request: Request,
    q: str = "", status: str = "",
    date_from: str = "", date_to: str = "",
    page: int = 1,
    db: Session = Depends(get_db)
):
    _require_session(request)
    query = db.query(Result)
    if q:
        like = f"%{q}%"
        query = (
            query.join(OrderItem).join(Order)
            .join(Order.patient)
            .filter(
                Order.order_number.ilike(like) |
                Order.patient.has(last_name=None) |  # placeholder — overridden below
                True
            )
        )
        # Simpler approach
        from ..models import Patient
        order_ids = [
            o.id for o in db.query(Order).join(Patient).filter(
                Order.order_number.ilike(like) |
                Patient.last_name.ilike(like) |
                Patient.first_name.ilike(like)
            ).all()
        ]
        item_ids = [i.id for i in db.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)).all()]
        query = db.query(Result).filter(Result.order_item_id.in_(item_ids))

    if status:
        query = query.filter(Result.status == status)
    if date_from:
        query = query.filter(Result.result_date >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(Result.result_date <= datetime.fromisoformat(date_to + "T23:59:59"))

    results = query.order_by(Result.result_date.desc()).offset((page - 1) * PER_PAGE).limit(PER_PAGE).all()
    return templates.TemplateResponse("results/list.html", {
        "request": request, "results": results,
        "q": q, "status_filter": status, "date_from": date_from, "date_to": date_to,
        "active_page": "results"
    })


@router.get("/enter/{order_id}", response_class=HTMLResponse)
def enter_results_form(order_id: int, request: Request, db: Session = Depends(get_db)):
    _require_session(request)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404)
    equipment = db.query(Equipment).filter(Equipment.status == "ACTIVE").all()

    # Group items by category
    items_with_cat = sorted(order.items, key=lambda i: i.test.category_id)
    grouped = []
    for cat_id, grp in groupby(items_with_cat, key=lambda i: i.test.category_id):
        cat = db.query(TestCategory).filter(TestCategory.id == cat_id).first()
        grouped.append((cat, list(grp)))

    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    return templates.TemplateResponse("results/enter.html", {
        "request": request, "order": order, "grouped_items": grouped,
        "equipment": equipment, "now": now, "active_page": "results"
    })


@router.post("/enter/{order_id}")
async def save_results(
    order_id: int,
    request: Request,
    equipment_id: str = Form(""),
    result_date: str = Form(""),
    action: str = Form("save"),
    db: Session = Depends(get_db)
):
    _require_session(request)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404)

    form = await request.form()
    eq_id = int(equipment_id) if equipment_id else None
    r_date = datetime.fromisoformat(result_date) if result_date else datetime.now()
    user_id = request.session.get("user_id")

    for item in order.items:
        value_key = f"value_{item.id}"
        obs_key = f"obs_{item.id}"
        value = form.get(value_key, "").strip()
        obs = form.get(obs_key, "").strip()

        if not value:
            continue

        is_abnormal, flag = _compute_flag(value, item.test.ref_min, item.test.ref_max)

        if item.result:
            # Update existing result (unless validated)
            if item.result.status != ResultStatus.VALIDATED:
                item.result.value = value
                item.result.equipment_id = eq_id
                item.result.result_date = r_date
                item.result.observations = obs or None
                item.result.is_abnormal = is_abnormal
                item.result.abnormal_flag = flag or None
                try:
                    item.result.numeric_value = float(value.replace(",", "."))
                except ValueError:
                    item.result.numeric_value = None
                item.result.unit = item.test.unit
                if action == "save_validate":
                    item.result.status = ResultStatus.VALIDATED
                    item.result.validated_by_id = user_id
                    item.result.validated_at = datetime.now()
                    item.status = OrderItemStatus.VALIDATED
                else:
                    item.result.status = ResultStatus.PENDING_VALIDATION
                    item.status = OrderItemStatus.RESULTED
        else:
            status = ResultStatus.VALIDATED if action == "save_validate" else ResultStatus.PENDING_VALIDATION
            result = Result(
                order_item_id=item.id,
                equipment_id=eq_id,
                value=value,
                unit=item.test.unit,
                result_date=r_date,
                observations=obs or None,
                is_abnormal=is_abnormal,
                abnormal_flag=flag or None,
                status=status,
            )
            try:
                result.numeric_value = float(value.replace(",", "."))
            except ValueError:
                result.numeric_value = None
            if action == "save_validate":
                result.validated_by_id = user_id
                result.validated_at = datetime.now()
                item.status = OrderItemStatus.VALIDATED
            else:
                item.status = OrderItemStatus.RESULTED
            db.add(result)

    # Update order status
    all_items = order.items
    if all(i.status in [OrderItemStatus.VALIDATED] for i in all_items):
        from ..models import OrderStatus
        order.status = OrderStatus.VALIDATED
    elif any(i.status in [OrderItemStatus.RESULTED, OrderItemStatus.VALIDATED] for i in all_items):
        from ..models import OrderStatus
        order.status = OrderStatus.IN_PROGRESS

    db.commit()
    return RedirectResponse(f"/orders/{order_id}", status_code=303)


@router.get("/validate/{result_id}", response_class=HTMLResponse)
def validate_result(result_id: int, request: Request, db: Session = Depends(get_db)):
    _require_session(request)
    result = db.query(Result).filter(Result.id == result_id).first()
    if not result:
        raise HTTPException(404)
    result.status = ResultStatus.VALIDATED
    result.validated_by_id = request.session.get("user_id")
    result.validated_at = datetime.now()
    result.order_item.status = OrderItemStatus.VALIDATED
    db.commit()
    return RedirectResponse(f"/orders/{result.order_item.order_id}", status_code=303)
