from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Order, OrderItem, Result, ResultStatus, Patient, Test, TestCategory, Equipment

router = APIRouter(prefix="/statistics", tags=["statistics"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def statistics(request: Request, period: int = 30, db: Session = Depends(get_db)):
    since = datetime.now() - timedelta(days=period)

    total_orders = db.query(Order).filter(Order.order_date >= since).count()
    total_results = db.query(Result).filter(Result.result_date >= since).count()
    validated = db.query(Result).filter(
        Result.result_date >= since, Result.status == ResultStatus.VALIDATED
    ).count()
    abnormal = db.query(Result).filter(
        Result.result_date >= since, Result.is_abnormal == True
    ).count()
    new_patients = db.query(Patient).filter(Patient.created_at >= since).count()

    # Average TAT (hours between order creation and first result)
    avg_tat = 24  # default placeholder

    stats = dict(
        total_orders=total_orders, total_results=total_results,
        validated=validated, abnormal=abnormal,
        new_patients=new_patients, avg_tat=avg_tat
    )

    # Trend data: daily orders & validated results
    trend_labels = []
    trend_orders = []
    trend_validated = []
    for i in range(period - 1, -1, -1):
        day = datetime.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59)
        if period <= 30:
            trend_labels.append(day.strftime("%d/%m"))
            orders_count = db.query(Order).filter(
                Order.order_date >= day_start, Order.order_date <= day_end
            ).count()
            val_count = db.query(Result).filter(
                Result.result_date >= day_start,
                Result.result_date <= day_end,
                Result.status == ResultStatus.VALIDATED
            ).count()
            trend_orders.append(orders_count)
            trend_validated.append(val_count)
        else:
            # Weekly buckets for longer periods
            if i % 7 == 0:
                week_end = day_start + timedelta(days=6)
                trend_labels.append(day.strftime("%d/%m"))
                orders_count = db.query(Order).filter(
                    Order.order_date >= day_start, Order.order_date <= week_end
                ).count()
                val_count = db.query(Result).filter(
                    Result.result_date >= day_start,
                    Result.result_date <= week_end,
                    Result.status == ResultStatus.VALIDATED
                ).count()
                trend_orders.append(orders_count)
                trend_validated.append(val_count)

    trend_data = dict(labels=trend_labels, orders=trend_orders, validated=trend_validated)

    # Urgency distribution
    urgency_counts = {"ROUTINE": 0, "URGENT": 0, "STAT": 0}
    for o in db.query(Order).filter(Order.order_date >= since).all():
        urgency_counts[o.urgency.value] = urgency_counts.get(o.urgency.value, 0) + 1
    urgency_data = dict(
        labels=list(urgency_counts.keys()),
        values=list(urgency_counts.values())
    )

    # By category
    categories = db.query(TestCategory).all()
    cat_labels, cat_values, cat_colors = [], [], []
    abnormal_labels, abnormal_values = [], []
    for cat in categories:
        test_ids = [t.id for t in cat.tests]
        if not test_ids:
            continue
        item_ids = [i.id for i in db.query(OrderItem).filter(OrderItem.test_id.in_(test_ids)).all()]
        count = db.query(Result).filter(
            Result.order_item_id.in_(item_ids),
            Result.result_date >= since
        ).count()
        abn_count = db.query(Result).filter(
            Result.order_item_id.in_(item_ids),
            Result.result_date >= since,
            Result.is_abnormal == True
        ).count()
        cat_labels.append(cat.name)
        cat_values.append(count)
        cat_colors.append(cat.color)
        if count > 0:
            abnormal_labels.append(cat.name)
            abnormal_values.append(round(abn_count / count * 100, 1))
        else:
            abnormal_labels.append(cat.name)
            abnormal_values.append(0)

    category_bar_data = dict(labels=cat_labels, values=cat_values, colors=cat_colors)
    abnormal_data = dict(labels=abnormal_labels, values=abnormal_values)

    # Top tests
    top_tests = []
    for test in db.query(Test).all():
        item_ids = [i.id for i in db.query(OrderItem).filter(OrderItem.test_id == test.id).all()]
        count = db.query(Result).filter(
            Result.order_item_id.in_(item_ids),
            Result.result_date >= since
        ).count()
        if count > 0:
            top_tests.append({
                "name": test.name,
                "category": test.category.name,
                "color": test.category.color,
                "count": count
            })
    top_tests.sort(key=lambda x: x["count"], reverse=True)
    top_tests = top_tests[:10]

    # Recent abnormal results
    recent_abnormal = []
    for r in db.query(Result).filter(
        Result.is_abnormal == True, Result.result_date >= since
    ).order_by(Result.result_date.desc()).limit(10).all():
        p = r.order_item.order.patient
        recent_abnormal.append({
            "test_name": r.order_item.test.name,
            "patient": f"{p.last_name}, {p.first_name}",
            "value": r.value,
            "flag": r.abnormal_flag or "",
            "date": r.result_date.strftime("%d/%m/%Y")
        })

    return templates.TemplateResponse("statistics/index.html", {
        "request": request,
        "stats": stats, "period": period,
        "trend_data": trend_data, "urgency_data": urgency_data,
        "category_bar_data": category_bar_data, "abnormal_data": abnormal_data,
        "top_tests": top_tests, "recent_abnormal": recent_abnormal,
        "active_page": "statistics"
    })
