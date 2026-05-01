from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Test, TestCategory

router = APIRouter(prefix="/catalog", tags=["catalog"])
templates = Jinja2Templates(directory="app/templates")


def _require_session(request: Request):
    if not request.session.get("user_id"):
        raise HTTPException(status_code=303, headers={"Location": "/auth/login"})


@router.get("", response_class=HTMLResponse)
def list_catalog(request: Request, q: str = "", category_id: str = "", db: Session = Depends(get_db)):
    _require_session(request)
    categories = db.query(TestCategory).filter(TestCategory.is_active == True).order_by(TestCategory.name).all()
    tests = db.query(Test).order_by(Test.category_id, Test.name).all()
    return templates.TemplateResponse("catalog/list.html", {
        "request": request, "categories": categories, "tests": tests,
        "q": q, "cat_filter": category_id, "active_page": "catalog"
    })


# ── Test CRUD ─────────────────────────────────────────────────────────────────

@router.get("/tests/new", response_class=HTMLResponse)
def new_test_form(request: Request, db: Session = Depends(get_db)):
    _require_session(request)
    categories = db.query(TestCategory).filter(TestCategory.is_active == True).all()
    return templates.TemplateResponse("catalog/test_form.html", {
        "request": request, "test": None, "categories": categories, "active_page": "catalog"
    })


@router.post("/tests/new")
async def create_test(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    abbreviation: str = Form(""),
    category_id: int = Form(...),
    method: str = Form(""),
    unit: str = Form(""),
    ref_min: str = Form(""),
    ref_max: str = Form(""),
    ref_range_male: str = Form(""),
    ref_range_female: str = Form(""),
    turnaround_hours: int = Form(24),
    price: float = Form(0.0),
    observations: str = Form(""),
    db: Session = Depends(get_db)
):
    _require_session(request)
    form = await request.form()
    test = Test(
        code=code.upper().strip(),
        name=name.strip(),
        abbreviation=abbreviation or None,
        category_id=category_id,
        method=method or None,
        unit=unit or None,
        ref_min=float(ref_min) if ref_min else None,
        ref_max=float(ref_max) if ref_max else None,
        ref_range_male=ref_range_male or None,
        ref_range_female=ref_range_female or None,
        turnaround_hours=turnaround_hours,
        price=price,
        requires_fasting="requires_fasting" in form,
        is_active="is_active" in form,
        observations=observations or None,
    )
    db.add(test)
    db.commit()
    return RedirectResponse("/catalog", status_code=303)


@router.get("/tests/{test_id}/edit", response_class=HTMLResponse)
def edit_test_form(test_id: int, request: Request, db: Session = Depends(get_db)):
    _require_session(request)
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(404)
    categories = db.query(TestCategory).filter(TestCategory.is_active == True).all()
    return templates.TemplateResponse("catalog/test_form.html", {
        "request": request, "test": test, "categories": categories, "active_page": "catalog"
    })


@router.post("/tests/{test_id}/edit")
async def update_test(
    test_id: int, request: Request,
    code: str = Form(...),
    name: str = Form(...),
    abbreviation: str = Form(""),
    category_id: int = Form(...),
    method: str = Form(""),
    unit: str = Form(""),
    ref_min: str = Form(""),
    ref_max: str = Form(""),
    ref_range_male: str = Form(""),
    ref_range_female: str = Form(""),
    turnaround_hours: int = Form(24),
    price: float = Form(0.0),
    observations: str = Form(""),
    db: Session = Depends(get_db)
):
    _require_session(request)
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(404)
    form = await request.form()
    test.code = code.upper().strip()
    test.name = name.strip()
    test.abbreviation = abbreviation or None
    test.category_id = category_id
    test.method = method or None
    test.unit = unit or None
    test.ref_min = float(ref_min) if ref_min else None
    test.ref_max = float(ref_max) if ref_max else None
    test.ref_range_male = ref_range_male or None
    test.ref_range_female = ref_range_female or None
    test.turnaround_hours = turnaround_hours
    test.price = price
    test.requires_fasting = "requires_fasting" in form
    test.is_active = "is_active" in form
    test.observations = observations or None
    db.commit()
    return RedirectResponse("/catalog", status_code=303)


# ── Category CRUD ─────────────────────────────────────────────────────────────

@router.get("/categories/new", response_class=HTMLResponse)
def new_category_form(request: Request):
    _require_session(request)
    return templates.TemplateResponse("catalog/category_form.html", {
        "request": request, "category": None, "active_page": "catalog"
    })


@router.post("/categories/new")
async def create_category(
    request: Request,
    name: str = Form(...),
    code: str = Form(...),
    description: str = Form(""),
    color: str = Form("#0d6efd"),
    db: Session = Depends(get_db)
):
    _require_session(request)
    cat = TestCategory(name=name, code=code.upper(), description=description or None, color=color)
    db.add(cat)
    db.commit()
    return RedirectResponse("/catalog", status_code=303)


@router.get("/categories/{cat_id}/edit", response_class=HTMLResponse)
def edit_category_form(cat_id: int, request: Request, db: Session = Depends(get_db)):
    _require_session(request)
    cat = db.query(TestCategory).filter(TestCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(404)
    return templates.TemplateResponse("catalog/category_form.html", {
        "request": request, "category": cat, "active_page": "catalog"
    })


@router.post("/categories/{cat_id}/edit")
async def update_category(
    cat_id: int, request: Request,
    name: str = Form(...),
    code: str = Form(...),
    description: str = Form(""),
    color: str = Form("#0d6efd"),
    db: Session = Depends(get_db)
):
    _require_session(request)
    cat = db.query(TestCategory).filter(TestCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(404)
    cat.name = name
    cat.code = code.upper()
    cat.description = description or None
    cat.color = color
    db.commit()
    return RedirectResponse("/catalog", status_code=303)
