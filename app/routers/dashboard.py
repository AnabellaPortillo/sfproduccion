from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Order, OrderItem, Result, ResultStatus, Patient, TestCategory

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/auth/login", status_code=303)

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = datetime.now().replace(hour=23, minute=59, second=59)

    orders_today = db.query(Order).filter(
        Order.order_date >= today_start, Order.order_date <= today_end
    ).count()

    pending_results_count = db.query(OrderItem).filter(
        OrderItem.status.in_(["PENDING", "IN_PROGRESS"])
    ).count()

    validated_today = db.query(Result).filter(
        Result.validated_at >= today_start,
        Result.validated_at <= today_end,
        Result.status == ResultStatus.VALIDATED
    ).count()

    total_patients = db.query(Patient).filter(Patient.is_active == True).count()

    recent_orders = db.query(Order).order_by(Order.order_date.desc()).limit(10).all()

    pending_validation = db.query(Result).filter(
        Result.status == ResultStatus.PENDING_VALIDATION
    ).order_by(Result.result_date.desc()).limit(8).all()

    # Last 7 days chart
    labels, values = [], []
    for i in range(6, -1, -1):
        day = datetime.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59)
        labels.append(day.strftime("%d/%m"))
        count = db.query(Order).filter(
            Order.order_date >= day_start, Order.order_date <= day_end
        ).count()
        values.append(count)
    orders_chart_data = dict(labels=labels, values=values)

    # Category distribution today
    categories = db.query(TestCategory).all()
    cat_labels, cat_values, cat_colors = [], [], []
    for cat in categories:
        test_ids = [t.id for t in cat.tests]
        if not test_ids:
            continue
        count = db.query(OrderItem).filter(
            OrderItem.test_id.in_(test_ids)
        ).join(Order).filter(
            Order.order_date >= today_start
        ).count()
        if count > 0:
            cat_labels.append(cat.name)
            cat_values.append(count)
            cat_colors.append(cat.color)

    category_chart_data = dict(labels=cat_labels, values=cat_values, colors=cat_colors)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": {
            "orders_today": orders_today,
            "pending_results": pending_results_count,
            "validated_today": validated_today,
            "total_patients": total_patients,
        },
        "recent_orders": recent_orders,
        "pending_validation": pending_validation,
        "orders_chart_data": orders_chart_data,
        "category_chart_data": category_chart_data,
        "active_page": "dashboard"
    })
