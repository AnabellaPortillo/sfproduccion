"""Router de importación de Excel — /import"""
import os
import tempfile
from datetime import date, datetime

from fastapi import APIRouter, Request, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Patient, Gender, Doctor, Order, OrderItem, OrderStatus,
    Urgency, Test, Result, ResultStatus, OrderItemStatus
)
from ..excel_import import parse_workbook, generate_template, ImportedProtocol

router = APIRouter(prefix="/import", tags=["import"])
templates = Jinja2Templates(directory="app/templates")


def _require_session(request: Request):
    if not request.session.get("user_id"):
        raise HTTPException(status_code=303, headers={"Location": "/auth/login"})


# ── Página principal de importación ──────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
def import_page(request: Request):
    _require_session(request)
    return templates.TemplateResponse("imports/index.html", {
        "request": request, "active_page": "import"
    })


# ── Descarga del template ─────────────────────────────────────────────────────

@router.get("/template")
def download_template(request: Request, db: Session = Depends(get_db)):
    _require_session(request)
    tests = db.query(Test).filter(Test.is_active == True).order_by(Test.category_id, Test.name).all()
    test_list = [{"name": t.name, "code": t.code} for t in tests]

    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    tmp.close()
    generate_template(tmp.name, test_list)
    return FileResponse(
        tmp.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="labcore_template_importacion.xlsx"
    )


# ── Preview: sube el archivo y muestra lo que se va a importar ───────────────

@router.post("/preview", response_class=HTMLResponse)
async def import_preview(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    _require_session(request)
    if not file.filename.endswith((".xlsx", ".xls")):
        return templates.TemplateResponse("imports/index.html", {
            "request": request, "active_page": "import",
            "error": "Solo se aceptan archivos .xlsx"
        })

    # Guardar en temp
    suffix = ".xlsx"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(await file.read())
    tmp.close()

    # Parsear
    try:
        protocols = parse_workbook(tmp.name)
    except Exception as e:
        os.unlink(tmp.name)
        return templates.TemplateResponse("imports/index.html", {
            "request": request, "active_page": "import",
            "error": f"Error al leer el archivo: {e}"
        })

    # Guardar path en sesión para el paso de confirmación
    request.session["import_tmp"] = tmp.name

    # Previsualización: enriquecer con info de matching
    all_tests = {t.code.upper(): t for t in db.query(Test).all()}
    all_tests_by_name = {t.name.lower(): t for t in db.query(Test).all()}

    preview = []
    for proto in protocols:
        if proto.sheet_name.upper() == "INSTRUCCIONES":
            continue
        # Verificar paciente existente
        existing_patient = None
        if proto.document_number:
            existing_patient = db.query(Patient).filter(
                Patient.document_number == proto.document_number
            ).first()

        # Match análisis
        matched_results = []
        for r in proto.results:
            test = (all_tests.get(r.test_name.upper()) or
                    all_tests_by_name.get(r.test_name.lower()))
            matched_results.append({
                "name": r.test_name,
                "value": r.value,
                "unit": r.unit,
                "matched": test.name if test else None,
                "found": test is not None,
            })

        preview.append({
            "sheet": proto.sheet_name,
            "protocol_number": proto.protocol_number,
            "order_date": proto.order_date.strftime("%d/%m/%Y") if proto.order_date else "—",
            "urgency": proto.urgency,
            "patient_name": f"{proto.last_name}, {proto.first_name}",
            "document": proto.document_number,
            "birth_date": proto.birth_date.strftime("%d/%m/%Y") if proto.birth_date else "—",
            "gender": proto.gender,
            "doctor": proto.doctor_name,
            "health_insurance": proto.health_insurance,
            "existing_patient": existing_patient.id if existing_patient else None,
            "existing_patient_name": f"{existing_patient.last_name}, {existing_patient.first_name}" if existing_patient else None,
            "results": matched_results,
            "warnings": proto.warnings,
            "results_count": len(proto.results),
            "unmatched": sum(1 for r in matched_results if not r["found"]),
        })

    return templates.TemplateResponse("imports/preview.html", {
        "request": request, "active_page": "import",
        "preview": preview, "filename": file.filename,
        "total_protocols": len(preview),
        "total_results": sum(p["results_count"] for p in preview),
    })


# ── Confirmación e importación real ──────────────────────────────────────────

@router.post("/confirm")
async def import_confirm(
    request: Request,
    db: Session = Depends(get_db)
):
    _require_session(request)
    tmp_path = request.session.pop("import_tmp", None)
    if not tmp_path or not os.path.exists(tmp_path):
        return RedirectResponse("/import", status_code=303)

    protocols = parse_workbook(tmp_path)
    os.unlink(tmp_path)

    all_tests_by_code = {t.code.upper(): t for t in db.query(Test).all()}
    all_tests_by_name = {t.name.lower(): t for t in db.query(Test).all()}
    user_id = request.session.get("user_id")

    imported_orders = 0
    imported_results = 0
    skipped = 0

    def _find_test(name: str) -> Test | None:
        return (all_tests_by_code.get(name.upper()) or
                all_tests_by_name.get(name.lower()))

    def _next_proto_number(order_date: date | None) -> str:
        d = order_date or date.today()
        prefix = d.strftime("%d%m%y")
        from ..models import Order as O
        last = db.query(O).filter(O.order_number.like(f"{prefix}%")).order_by(O.order_number.desc()).first()
        seq = (int(last.order_number[6:]) + 1) if last else 1
        return f"{prefix}{seq:03d}"

    for proto in protocols:
        if proto.sheet_name.upper() == "INSTRUCCIONES":
            continue
        if not proto.last_name and not proto.document_number:
            skipped += 1
            continue

        # ── Paciente ─────────────────────────────────────────────────────────
        patient = None
        if proto.document_number:
            patient = db.query(Patient).filter(
                Patient.document_number == proto.document_number
            ).first()

        if not patient:
            patient = Patient(
                document_type="DNI",
                document_number=proto.document_number or f"IMP-{datetime.now().timestamp():.0f}",
                last_name=proto.last_name or "IMPORTADO",
                first_name=proto.first_name or "",
                birth_date=proto.birth_date or date(1900, 1, 1),
                gender=Gender(proto.gender) if proto.gender in ("M", "F", "O") else Gender.M,
                health_insurance=proto.health_insurance or None,
                insurance_number=proto.insurance_number or None,
            )
            db.add(patient)
            db.flush()

        # ── Médico (buscar por apellido) ──────────────────────────────────────
        doctor_id = None
        if proto.doctor_name:
            # Intenta encontrarlo por apellido (insensitive)
            parts = proto.doctor_name.replace("Dr.", "").replace("Dra.", "").strip().split()
            if parts:
                doc = db.query(Doctor).filter(
                    Doctor.last_name.ilike(f"%{parts[0]}%")
                ).first()
                if not doc and len(parts) > 1:
                    doc = db.query(Doctor).filter(
                        Doctor.last_name.ilike(f"%{parts[-1]}%")
                    ).first()
                if doc:
                    doctor_id = doc.id

        # ── Orden ─────────────────────────────────────────────────────────────
        order_date_dt = (datetime.combine(proto.order_date, datetime.min.time())
                         if proto.order_date else datetime.now())
        order_number = (proto.protocol_number.strip()
                        if proto.protocol_number
                        else _next_proto_number(proto.order_date))

        # Evitar duplicados por número de protocolo
        existing_order = db.query(Order).filter(Order.order_number == order_number).first()
        if existing_order:
            skipped += 1
            continue

        order = Order(
            order_number=order_number,
            patient_id=patient.id,
            doctor_id=doctor_id,
            urgency=Urgency(proto.urgency) if proto.urgency in ("ROUTINE", "URGENT", "STAT") else Urgency.ROUTINE,
            order_date=order_date_dt,
            status=OrderStatus.VALIDATED,
            observations=proto.observations or None,
            created_by_id=user_id,
        )
        db.add(order)
        db.flush()

        total_price = 0.0
        for res in proto.results:
            if not res.test_name:
                continue
            test = _find_test(res.test_name)
            if test:
                total_price += test.price or 0.0

            item = OrderItem(
                order_id=order.id,
                test_id=test.id if test else None,
                status=OrderItemStatus.VALIDATED if res.value else OrderItemStatus.PENDING,
                notes=f"Importado desde Excel. Análisis: {res.test_name}" if not test else None,
            )

            # Si no hay test en catálogo, necesitamos un test_id válido; creamos uno temporal
            if not test:
                # Buscar o crear un test genérico "Importado"
                from ..models import TestCategory
                cat = db.query(TestCategory).first()
                if cat:
                    tmp_test = Test(
                        code=f"IMP-{res.test_name[:10].upper().replace(' ','')}",
                        name=res.test_name,
                        category_id=cat.id,
                        unit=res.unit or None,
                        is_active=False,  # marcado como inactivo hasta revisión
                    )
                    db.add(tmp_test)
                    db.flush()
                    item.test_id = tmp_test.id
                    all_tests_by_name[res.test_name.lower()] = tmp_test

            db.add(item)
            db.flush()

            if res.value and item.test_id:
                is_abn, flag = False, ""
                t = test or db.query(Test).filter(Test.id == item.test_id).first()
                try:
                    v = float(res.value.replace(",", "."))
                    if t and t.ref_max and v > t.ref_max:
                        is_abn, flag = True, "H"
                    elif t and t.ref_min and v < t.ref_min:
                        is_abn, flag = True, "L"
                except (ValueError, AttributeError):
                    pass
                result = Result(
                    order_item_id=item.id,
                    value=res.value,
                    unit=res.unit or (t.unit if t else None),
                    observations=res.observations or None,
                    is_abnormal=is_abn,
                    abnormal_flag=flag or None,
                    status=ResultStatus.VALIDATED,
                    validated_by_id=user_id,
                    validated_at=order_date_dt,
                    result_date=order_date_dt,
                )
                try:
                    result.numeric_value = float(res.value.replace(",", "."))
                except (ValueError, AttributeError):
                    pass
                db.add(result)
                imported_results += 1

        order.total_price = total_price
        imported_orders += 1

    db.commit()

    # Guardar resumen en sesión para mostrarlo
    request.session["import_result"] = {
        "orders": imported_orders,
        "results": imported_results,
        "skipped": skipped,
    }
    return RedirectResponse("/import/done", status_code=303)


@router.get("/done", response_class=HTMLResponse)
def import_done(request: Request):
    _require_session(request)
    result = request.session.pop("import_result", {"orders": 0, "results": 0, "skipped": 0})
    return templates.TemplateResponse("imports/done.html", {
        "request": request, "active_page": "import", **result
    })
