"""
Startup logic: migrate DB columns and configure test panels.
Run once at app startup — all operations are idempotent.
"""
from sqlalchemy import text
from .database import engine, SessionLocal
from .models import Test, TestCategory


def migrate_columns():
    """Add new columns to existing SQLite tables without Alembic."""
    with engine.connect() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(tests)"))]
        if "is_panel" not in cols:
            conn.execute(text("ALTER TABLE tests ADD COLUMN is_panel BOOLEAN DEFAULT 0"))
        if "panel_components" not in cols:
            conn.execute(text("ALTER TABLE tests ADD COLUMN panel_components TEXT"))
        conn.commit()


# Complete hemogram sub-tests (HCM, CHCM, RDW + differential)
_HEMOGRAM_SUBTESTS = [
    dict(code="HCM",  name="Hemoglobina corpuscular media",        abbreviation="HCM",
         unit="pg",       ref_min=27.0, ref_max=33.0,
         ref_range_male="27-33", ref_range_female="27-33"),
    dict(code="CHCM", name="Concentración de Hb corpuscular media", abbreviation="CHCM",
         unit="g/dL",     ref_min=32.0, ref_max=36.0,
         ref_range_male="32-36", ref_range_female="32-36"),
    dict(code="RDW",  name="Amplitud de distribución eritrocitaria", abbreviation="RDW",
         unit="%",        ref_min=11.5, ref_max=14.5,
         ref_range_male="11.5-14.5", ref_range_female="11.5-14.5"),
    dict(code="NEUT", name="Neutrófilos",   abbreviation="Neut",
         unit="%",        ref_min=50.0, ref_max=70.0,
         ref_range_male="50-70", ref_range_female="50-70"),
    dict(code="LINF", name="Linfocitos",    abbreviation="Linf",
         unit="%",        ref_min=20.0, ref_max=40.0,
         ref_range_male="20-40", ref_range_female="20-40"),
    dict(code="MONO", name="Monocitos",     abbreviation="Mono",
         unit="%",        ref_min=2.0,  ref_max=8.0,
         ref_range_male="2-8", ref_range_female="2-8"),
    dict(code="EOS",  name="Eosinófilos",   abbreviation="Eos",
         unit="%",        ref_min=1.0,  ref_max=4.0,
         ref_range_male="1-4", ref_range_female="1-4"),
    dict(code="BASO", name="Basófilos",     abbreviation="Baso",
         unit="%",        ref_min=0.0,  ref_max=1.0,
         ref_range_male="0-1", ref_range_female="0-1"),
]

# Panel definitions: panel_code -> [component codes in display order]
PANELS = {
    "HMG": ["GR", "GB", "HB", "HTO", "VCM", "HCM", "CHCM", "RDW", "PLQ",
            "NEUT", "LINF", "MONO", "EOS", "BASO"],
}


def setup_panels():
    db = SessionLocal()
    try:
        hema_cat = db.query(TestCategory).filter(TestCategory.code == "HEMA").first()
        if not hema_cat:
            return

        # Add missing sub-tests
        for t in _HEMOGRAM_SUBTESTS:
            if not db.query(Test).filter(Test.code == t["code"]).first():
                db.add(Test(
                    category_id=hema_cat.id,
                    turnaround_hours=2,
                    price=0.0,
                    is_active=True,
                    **t,
                ))
        db.flush()

        # Configure panel tests
        for panel_code, components in PANELS.items():
            panel_test = db.query(Test).filter(Test.code == panel_code).first()
            if panel_test:
                panel_test.is_panel = True
                panel_test.panel_components = ",".join(components)

        db.commit()
    finally:
        db.close()
