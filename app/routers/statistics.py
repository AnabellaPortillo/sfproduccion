from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Order, OrderItem, Result, ResultStatus, Patient, Test, TestCategory

router = APIRouter(prefix="/statistics", tags=["statistics"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def statistics(request: Request, period: int = 30, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/auth/login", status_code=303)

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

    stats = dict(
        total_orders=total_orders, total_results=total_results,
        validated=validated, abnormal=abnormal,
        new_patients=new_patients, avg_tat=24
    )

    # ── Tendencia diaria/semanal ──────────────────────────────────────────────
    trend_labels, trend_orders, trend_validated = [], [], []
    step = 1 if period <= 30 else 7
    i = period - 1
    while i >= 0:
        day = datetime.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=step) - timedelta(seconds=1)
        trend_labels.append(day.strftime("%d/%m"))
        trend_orders.append(db.query(Order).filter(
            Order.order_date >= day_start, Order.order_date <= day_end
        ).count())
        trend_validated.append(db.query(Result).filter(
            Result.result_date >= day_start, Result.result_date <= day_end,
            Result.status == ResultStatus.VALIDATED
        ).count())
        i -= step
    trend_data = dict(labels=trend_labels, orders=trend_orders, validated=trend_validated)

    # ── Distribución por urgencia ─────────────────────────────────────────────
    urgency_counts = {"ROUTINE": 0, "URGENT": 0, "STAT": 0}
    for o in db.query(Order).filter(Order.order_date >= since).all():
        urgency_counts[o.urgency.value] = urgency_counts.get(o.urgency.value, 0) + 1
    urgency_data = dict(labels=list(urgency_counts.keys()), values=list(urgency_counts.values()))

    # ── Por categoría ─────────────────────────────────────────────────────────
    cat_labels, cat_values, cat_colors, abnormal_labels, abnormal_values = [], [], [], [], []
    for cat in db.query(TestCategory).all():
        test_ids = [t.id for t in cat.tests]
        if not test_ids:
            continue
        item_ids = [i.id for i in db.query(OrderItem).filter(OrderItem.test_id.in_(test_ids)).all()]
        count = db.query(Result).filter(
            Result.order_item_id.in_(item_ids), Result.result_date >= since
        ).count()
        abn = db.query(Result).filter(
            Result.order_item_id.in_(item_ids), Result.result_date >= since,
            Result.is_abnormal == True
        ).count()
        cat_labels.append(cat.name)
        cat_values.append(count)
        cat_colors.append(cat.color)
        abnormal_labels.append(cat.name)
        abnormal_values.append(round(abn / count * 100, 1) if count else 0)

    category_bar_data = dict(labels=cat_labels, values=cat_values, colors=cat_colors)
    abnormal_data = dict(labels=abnormal_labels, values=abnormal_values)

    # ── Top 10 determinaciones ────────────────────────────────────────────────
    top_tests = []
    for test in db.query(Test).all():
        item_ids = [i.id for i in db.query(OrderItem).filter(OrderItem.test_id == test.id).all()]
        count = db.query(Result).filter(
            Result.order_item_id.in_(item_ids), Result.result_date >= since
        ).count()
        if count > 0:
            abn = db.query(Result).filter(
                Result.order_item_id.in_(item_ids), Result.result_date >= since,
                Result.is_abnormal == True
            ).count()
            top_tests.append({
                "name": test.name, "code": test.code,
                "category": test.category.name, "color": test.category.color,
                "count": count, "abnormal": abn,
                "pct_abnormal": round(abn / count * 100, 1) if count else 0,
            })
    top_tests.sort(key=lambda x: x["count"], reverse=True)

    # ── Estadísticas por determinación individual ─────────────────────────────
    det_stats = []
    for test in db.query(Test).order_by(Test.category_id, Test.name).all():
        item_ids = [i.id for i in db.query(OrderItem).filter(OrderItem.test_id == test.id).all()]
        results = db.query(Result).filter(
            Result.order_item_id.in_(item_ids),
            Result.result_date >= since,
            Result.numeric_value.isnot(None)
        ).all()
        count_total = db.query(Result).filter(
            Result.order_item_id.in_(item_ids), Result.result_date >= since
        ).count()
        if count_total == 0:
            continue
        abn = sum(1 for r in results if r.is_abnormal)
        highs = sum(1 for r in results if r.abnormal_flag == "H")
        lows = sum(1 for r in results if r.abnormal_flag == "L")
        numeric_vals = [r.numeric_value for r in results]
        avg = round(sum(numeric_vals) / len(numeric_vals), 2) if numeric_vals else None
        mn  = round(min(numeric_vals), 2) if numeric_vals else None
        mx  = round(max(numeric_vals), 2) if numeric_vals else None
        det_stats.append({
            "id": test.id,
            "name": test.name,
            "code": test.code,
            "category": test.category.name,
            "color": test.category.color,
            "unit": test.unit or "",
            "ref": (f"{test.ref_min}–{test.ref_max}" if test.ref_min is not None and test.ref_max is not None
                    else test.ref_range_male or ""),
            "count": count_total,
            "abnormal": abn,
            "highs": highs,
            "lows": lows,
            "pct_abn": round(abn / count_total * 100, 1) if count_total else 0,
            "avg": avg,
            "min": mn,
            "max": mx,
        })

    # ── Anormales recientes ───────────────────────────────────────────────────
    recent_abnormal = []
    for r in db.query(Result).filter(
        Result.is_abnormal == True, Result.result_date >= since
    ).order_by(Result.result_date.desc()).limit(10).all():
        p = r.order_item.order.patient
        recent_abnormal.append({
            "protocol": r.order_item.order.order_number,
            "test_name": r.order_item.test.name,
            "patient": f"{p.last_name}, {p.first_name}",
            "value": r.value,
            "unit": r.unit or "",
            "flag": r.abnormal_flag or "",
            "date": r.result_date.strftime("%d/%m/%Y"),
        })

    return templates.TemplateResponse("statistics/index.html", {
        "request": request,
        "stats": stats, "period": period,
        "trend_data": trend_data, "urgency_data": urgency_data,
        "category_bar_data": category_bar_data, "abnormal_data": abnormal_data,
        "top_tests": top_tests[:10], "recent_abnormal": recent_abnormal,
        "det_stats": det_stats,
        "active_page": "statistics"
    })


@router.get("/determinacion/{test_id}", response_class=HTMLResponse)
def stat_by_test(test_id: int, request: Request, period: int = 30, db: Session = Depends(get_db)):
    """Estadística detallada de una determinación individual."""
    if not request.session.get("user_id"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/auth/login", status_code=303)

    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        from fastapi import HTTPException
        raise HTTPException(404)

    since = datetime.now() - timedelta(days=period)
    item_ids = [i.id for i in db.query(OrderItem).filter(OrderItem.test_id == test_id).all()]
    results = db.query(Result).filter(
        Result.order_item_id.in_(item_ids),
        Result.result_date >= since
    ).order_by(Result.result_date.desc()).all()

    # Distribución de valores numéricos para histograma
    numeric = [r for r in results if r.numeric_value is not None]
    hist_data = {"labels": [], "values": [], "colors": []}
    if numeric and test.ref_min is not None and test.ref_max is not None:
        bucket_size = (test.ref_max - test.ref_min) / 5 or 1
        low_limit = test.ref_min - 2 * bucket_size
        high_limit = test.ref_max + 2 * bucket_size
        buckets_n = 9
        step = (high_limit - low_limit) / buckets_n
        counts = [0] * buckets_n
        for r in numeric:
            idx = int((r.numeric_value - low_limit) / step)
            idx = max(0, min(idx, buckets_n - 1))
            counts[idx] += 1
        for bi in range(buckets_n):
            lo = round(low_limit + bi * step, 2)
            hi = round(low_limit + (bi + 1) * step, 2)
            hist_data["labels"].append(f"{lo}-{hi}")
            hist_data["values"].append(counts[bi])
            in_range = test.ref_min <= lo and hi <= test.ref_max
            hist_data["colors"].append("rgba(16,185,129,0.7)" if in_range else "rgba(239,68,68,0.6)")

    # Trend por día
    trend_labels, trend_counts, trend_abn = [], [], []
    for i in range(29, -1, -1):
        day = datetime.now() - timedelta(days=i)
        ds = day.replace(hour=0, minute=0, second=0, microsecond=0)
        de = ds + timedelta(days=1)
        day_res = [r for r in results if ds <= r.result_date < de]
        trend_labels.append(day.strftime("%d/%m"))
        trend_counts.append(len(day_res))
        trend_abn.append(sum(1 for r in day_res if r.is_abnormal))

    recent = []
    for r in results[:20]:
        p = r.order_item.order.patient
        recent.append({
            "protocol": r.order_item.order.order_number,
            "patient": f"{p.last_name}, {p.first_name}",
            "doc": p.document_number,
            "value": r.value,
            "unit": r.unit or test.unit or "",
            "flag": r.abnormal_flag or "",
            "status": r.status.value,
            "date": r.result_date.strftime("%d/%m/%Y %H:%M"),
            "order_id": r.order_item.order_id,
        })

    numeric_vals = [r.numeric_value for r in numeric]
    summary = {
        "count": len(results),
        "abnormal": sum(1 for r in results if r.is_abnormal),
        "highs": sum(1 for r in results if r.abnormal_flag == "H"),
        "lows": sum(1 for r in results if r.abnormal_flag == "L"),
        "avg": round(sum(numeric_vals) / len(numeric_vals), 2) if numeric_vals else None,
        "min": round(min(numeric_vals), 2) if numeric_vals else None,
        "max": round(max(numeric_vals), 2) if numeric_vals else None,
    }

    return templates.TemplateResponse("statistics/determinacion.html", {
        "request": request, "test": test, "period": period,
        "summary": summary, "recent": recent,
        "hist_data": hist_data,
        "trend_data": {"labels": trend_labels, "counts": trend_counts, "abnormal": trend_abn},
        "active_page": "statistics"
    })
