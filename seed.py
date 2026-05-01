"""Seed inicial: categorías, análisis del nomenclador, equipos, médicos, usuarios y pacientes demo."""
from datetime import date, datetime, timedelta
import random
from passlib.context import CryptContext
from app.database import SessionLocal, engine, Base
from app.models import (
    User, UserRole, Patient, Gender, Doctor,
    TestCategory, Test, Equipment, EquipmentStatus,
    Order, OrderItem, OrderStatus, Urgency,
    Result, ResultStatus, OrderItemStatus
)

Base.metadata.create_all(bind=engine)
db = SessionLocal()
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Limpiar ──────────────────────────────────────────────────────────────────
for m in [Result, OrderItem, Order, Test, TestCategory, Equipment, Doctor, Patient, User]:
    db.query(m).delete()
db.commit()

# ── Usuarios ─────────────────────────────────────────────────────────────────
users = [
    User(username="admin",      full_name="Administrador Sistema", email="admin@labcore.ar",      hashed_password=pwd.hash("admin123"),    role=UserRole.ADMIN),
    User(username="supervisor", full_name="Laura Fernández",       email="laura@labcore.ar",       hashed_password=pwd.hash("super123"),    role=UserRole.SUPERVISOR),
    User(username="tecnico1",   full_name="Carlos Gómez",          email="cgomez@labcore.ar",      hashed_password=pwd.hash("tec123"),      role=UserRole.TECHNICIAN),
    User(username="recepcion",  full_name="María López",           email="mlopez@labcore.ar",      hashed_password=pwd.hash("rec123"),      role=UserRole.RECEPTIONIST),
]
db.add_all(users)
db.flush()

# ── Médicos ───────────────────────────────────────────────────────────────────
doctors = [
    Doctor(last_name="RODRIGUEZ",  first_name="Jorge",    specialty="Clínica Médica",  license_number="MP 12345", phone="011-4523-1234"),
    Doctor(last_name="MARTINEZ",   first_name="Ana",      specialty="Cardiología",     license_number="MP 23456", phone="011-4512-5678"),
    Doctor(last_name="SANCHEZ",    first_name="Roberto",  specialty="Endocrinología",  license_number="MP 34567", phone="011-4556-7890"),
    Doctor(last_name="GARCIA",     first_name="Patricia", specialty="Pediatría",       license_number="MP 45678", phone="011-4578-2345"),
    Doctor(last_name="Lopez",      first_name="Miguel",   specialty="Nefrología",      license_number="MP 56789", phone="011-4534-6789"),
    Doctor(last_name="GONZALEZ",   first_name="Silvia",   specialty="Reumatología",    license_number="MP 67890", phone="011-4567-3456"),
]
db.add_all(doctors)
db.flush()

# ── Categorías del nomenclador ────────────────────────────────────────────────
cat_hema  = TestCategory(name="Hematología",       code="HEMA",  color="#dc2626", description="Hemograma y serie roja/blanca")
cat_bioquim = TestCategory(name="Bioquímica",      code="BIOQ",  color="#2563eb", description="Glucosa, lípidos, función hepática y renal")
cat_coag  = TestCategory(name="Coagulación",       code="COAG",  color="#7c3aed", description="Hemostasia y coagulación")
cat_orina = TestCategory(name="Orina",             code="ORIN",  color="#d97706", description="Análisis de orina y sedimento")
cat_hormo = TestCategory(name="Hormonas",          code="HORM",  color="#059669", description="Perfil hormonal tiroideo, sexual y suprarrenal")
cat_inmuno= TestCategory(name="Inmunología",       code="INMU",  color="#0891b2", description="Serología, autoanticuerpos, marcadores")
cat_micro = TestCategory(name="Microbiología",     code="MICR",  color="#65a30d", description="Cultivos y antibiogramas")
cat_gases = TestCategory(name="Gases en Sangre",   code="GASE",  color="#e11d48", description="Gasometría arterial y venosa")
db.add_all([cat_hema, cat_bioquim, cat_coag, cat_orina, cat_hormo, cat_inmuno, cat_micro, cat_gases])
db.flush()

# ── Análisis — Nomenclador Nacional (más comunes) ─────────────────────────────
tests = [
    # HEMATOLOGÍA
    Test(code="HMG",   name="Hemograma completo",              abbreviation="HMG",  category_id=cat_hema.id,   unit="múltiple",       turnaround_hours=2,  price=850.0),
    Test(code="GR",    name="Glóbulos rojos",                  abbreviation="GR",   category_id=cat_hema.id,   unit="x10⁶/µL",        ref_min=4.2, ref_max=5.8,   ref_range_male="4.5-5.8", ref_range_female="4.2-5.2", turnaround_hours=2,  price=0.0),
    Test(code="GB",    name="Glóbulos blancos",                abbreviation="GB",   category_id=cat_hema.id,   unit="x10³/µL",        ref_min=4.5, ref_max=11.0,  ref_range_male="4.5-11.0", ref_range_female="4.5-11.0", turnaround_hours=2, price=0.0),
    Test(code="HB",    name="Hemoglobina",                     abbreviation="Hb",   category_id=cat_hema.id,   unit="g/dL",           ref_min=12.0,ref_max=17.5,  ref_range_male="13.5-17.5", ref_range_female="12.0-16.0", turnaround_hours=2, price=0.0),
    Test(code="HTO",   name="Hematocrito",                     abbreviation="Hto",  category_id=cat_hema.id,   unit="%",              ref_min=37.0,ref_max=52.0,  ref_range_male="40-52", ref_range_female="37-47", turnaround_hours=2, price=0.0),
    Test(code="VCM",   name="Volumen corpuscular medio",        abbreviation="VCM",  category_id=cat_hema.id,   unit="fL",             ref_min=80.0,ref_max=100.0, turnaround_hours=2,  price=0.0),
    Test(code="PLQ",   name="Plaquetas",                        abbreviation="Plaq", category_id=cat_hema.id,   unit="x10³/µL",        ref_min=150.0,ref_max=400.0,turnaround_hours=2,  price=0.0),
    Test(code="VSG",   name="Velocidad de sedimentación globular", abbreviation="VSG", category_id=cat_hema.id, unit="mm/1ª hora",    ref_range_male="0-15", ref_range_female="0-20", turnaround_hours=2, price=350.0),
    Test(code="RETICULO", name="Reticulocitos",                 abbreviation="Retic",category_id=cat_hema.id,  unit="%",              ref_min=0.5, ref_max=2.0,   turnaround_hours=4,  price=400.0),
    Test(code="FROTIS", name="Frotis de sangre periférica",    abbreviation="Frotis",category_id=cat_hema.id,  unit="informe",        turnaround_hours=24, price=600.0),

    # BIOQUÍMICA
    Test(code="GLU",   name="Glucemia",                         abbreviation="Glu",  category_id=cat_bioquim.id,unit="mg/dL",          ref_min=70.0,ref_max=100.0, turnaround_hours=2,  price=300.0, requires_fasting=True),
    Test(code="HBA1C", name="Hemoglobina glicosilada (HbA1c)",  abbreviation="HbA1c",category_id=cat_bioquim.id,unit="%",             ref_range_male="< 5.7%", ref_range_female="< 5.7%", turnaround_hours=4, price=900.0),
    Test(code="CREA",  name="Creatinina",                       abbreviation="Crea", category_id=cat_bioquim.id,unit="mg/dL",          ref_range_male="0.7-1.2", ref_range_female="0.5-1.1", ref_min=0.5, ref_max=1.2, turnaround_hours=2, price=350.0),
    Test(code="UREA",  name="Urea",                             abbreviation="Urea", category_id=cat_bioquim.id,unit="mg/dL",          ref_min=15.0,ref_max=45.0,  turnaround_hours=2,  price=300.0),
    Test(code="ACUR",  name="Ácido úrico",                      abbreviation="AcUr", category_id=cat_bioquim.id,unit="mg/dL",          ref_range_male="3.5-7.2", ref_range_female="2.6-6.0", ref_min=2.6, ref_max=7.2, turnaround_hours=2, price=300.0),
    Test(code="COL",   name="Colesterol total",                  abbreviation="Col",  category_id=cat_bioquim.id,unit="mg/dL",          ref_max=200.0, ref_range_male="< 200", ref_range_female="< 200", turnaround_hours=2, price=300.0, requires_fasting=True),
    Test(code="HDL",   name="Colesterol HDL",                   abbreviation="HDL",  category_id=cat_bioquim.id,unit="mg/dL",          ref_range_male="> 40", ref_range_female="> 50", turnaround_hours=2, price=350.0, requires_fasting=True),
    Test(code="LDL",   name="Colesterol LDL",                   abbreviation="LDL",  category_id=cat_bioquim.id,unit="mg/dL",          ref_max=130.0, ref_range_male="< 130", ref_range_female="< 130", turnaround_hours=2, price=350.0, requires_fasting=True),
    Test(code="TRG",   name="Triglicéridos",                    abbreviation="TRG",  category_id=cat_bioquim.id,unit="mg/dL",          ref_max=150.0, ref_range_male="< 150", ref_range_female="< 150", turnaround_hours=2, price=300.0, requires_fasting=True),
    Test(code="TGO",   name="TGO (AST)",                        abbreviation="TGO",  category_id=cat_bioquim.id,unit="U/L",            ref_min=0.0, ref_max=40.0,  turnaround_hours=2,  price=300.0),
    Test(code="TGP",   name="TGP (ALT)",                        abbreviation="TGP",  category_id=cat_bioquim.id,unit="U/L",            ref_min=0.0, ref_max=41.0,  turnaround_hours=2,  price=300.0),
    Test(code="GGT",   name="Gamma-glutamiltransferasa (GGT)",  abbreviation="GGT",  category_id=cat_bioquim.id,unit="U/L",            ref_range_male="10-71", ref_range_female="6-42", ref_min=6, ref_max=71, turnaround_hours=2, price=350.0),
    Test(code="FAL",   name="Fosfatasa alcalina",               abbreviation="FAL",  category_id=cat_bioquim.id,unit="U/L",            ref_min=44.0,ref_max=147.0,  turnaround_hours=2,  price=300.0),
    Test(code="BT",    name="Bilirrubina total",                 abbreviation="BT",   category_id=cat_bioquim.id,unit="mg/dL",          ref_min=0.2, ref_max=1.2,   turnaround_hours=2,  price=300.0),
    Test(code="BD",    name="Bilirrubina directa",              abbreviation="BD",   category_id=cat_bioquim.id,unit="mg/dL",          ref_max=0.3,  turnaround_hours=2,  price=300.0),
    Test(code="PT",    name="Proteínas totales",                 abbreviation="PT",   category_id=cat_bioquim.id,unit="g/dL",           ref_min=6.0, ref_max=8.3,   turnaround_hours=2,  price=300.0),
    Test(code="ALB",   name="Albúmina",                         abbreviation="Alb",  category_id=cat_bioquim.id,unit="g/dL",           ref_min=3.5, ref_max=5.0,   turnaround_hours=2,  price=300.0),
    Test(code="NA",    name="Sodio (Na⁺)",                      abbreviation="Na",   category_id=cat_bioquim.id,unit="mEq/L",          ref_min=136.0,ref_max=145.0, turnaround_hours=2,  price=300.0),
    Test(code="K",     name="Potasio (K⁺)",                     abbreviation="K",    category_id=cat_bioquim.id,unit="mEq/L",          ref_min=3.5, ref_max=5.1,   turnaround_hours=2,  price=300.0),
    Test(code="CL",    name="Cloruro (Cl⁻)",                    abbreviation="Cl",   category_id=cat_bioquim.id,unit="mEq/L",          ref_min=98.0,ref_max=106.0,  turnaround_hours=2,  price=300.0),
    Test(code="CA",    name="Calcio total",                      abbreviation="Ca",   category_id=cat_bioquim.id,unit="mg/dL",          ref_min=8.5, ref_max=10.5,  turnaround_hours=2,  price=300.0),
    Test(code="FE",    name="Ferremia (hierro sérico)",          abbreviation="Fe",   category_id=cat_bioquim.id,unit="µg/dL",          ref_range_male="70-180", ref_range_female="60-170", ref_min=60, ref_max=180, turnaround_hours=4, price=400.0, requires_fasting=True),
    Test(code="FERR",  name="Ferritina",                         abbreviation="Ferr", category_id=cat_bioquim.id,unit="ng/mL",          ref_range_male="30-400", ref_range_female="13-150", ref_min=13, ref_max=400, turnaround_hours=4, price=950.0),
    Test(code="TIBC",  name="TIBC (capacidad fijación hierro)", abbreviation="TIBC", category_id=cat_bioquim.id,unit="µg/dL",          ref_min=250.0,ref_max=370.0, turnaround_hours=4,  price=500.0),
    Test(code="PCR",   name="Proteína C reactiva (PCR)",         abbreviation="PCR",  category_id=cat_bioquim.id,unit="mg/L",           ref_max=5.0,  turnaround_hours=2,  price=600.0),
    Test(code="LDH",   name="Lactato deshidrogenasa (LDH)",     abbreviation="LDH",  category_id=cat_bioquim.id,unit="U/L",            ref_min=120.0,ref_max=246.0, turnaround_hours=2,  price=400.0),
    Test(code="CPK",   name="Creatinfosfoquinasa (CPK)",         abbreviation="CPK",  category_id=cat_bioquim.id,unit="U/L",            ref_range_male="24-195", ref_range_female="24-170", ref_min=24, ref_max=195, turnaround_hours=2, price=450.0),
    Test(code="AMILASA",name="Amilasa",                         abbreviation="Amil", category_id=cat_bioquim.id,unit="U/L",            ref_min=28.0,ref_max=100.0,  turnaround_hours=2,  price=400.0),
    Test(code="LIPASA", name="Lipasa",                           abbreviation="Lip",  category_id=cat_bioquim.id,unit="U/L",            ref_min=13.0,ref_max=60.0,   turnaround_hours=2,  price=500.0),
    Test(code="B12",    name="Vitamina B12",                     abbreviation="B12",  category_id=cat_bioquim.id,unit="pg/mL",          ref_min=200.0,ref_max=900.0, turnaround_hours=24, price=1200.0),
    Test(code="FOLATO", name="Ácido fólico (folato)",            abbreviation="Folat",category_id=cat_bioquim.id,unit="ng/mL",          ref_min=3.0, ref_max=17.0,  turnaround_hours=24, price=1100.0),
    Test(code="VITD",   name="Vitamina D (25-OH)",               abbreviation="VitD", category_id=cat_bioquim.id,unit="ng/mL",          ref_min=30.0,ref_max=100.0,  turnaround_hours=24, price=2500.0),

    # COAGULACIÓN
    Test(code="KPTT",  name="KPTT (tiempo parcial tromboplastina)", abbreviation="KPTT", category_id=cat_coag.id, unit="seg", ref_min=25.0, ref_max=35.0, turnaround_hours=2, price=400.0),
    Test(code="TP",    name="Tiempo de protrombina (TP/RIN)",    abbreviation="TP",   category_id=cat_coag.id,  unit="seg / INR",      ref_range_male="11-14 seg / INR < 1.2", turnaround_hours=2, price=400.0),
    Test(code="FIBRI", name="Fibrinógeno",                        abbreviation="Fibri",category_id=cat_coag.id,  unit="mg/dL",          ref_min=200.0,ref_max=400.0, turnaround_hours=4,  price=600.0),
    Test(code="DDIMER",name="Dímero D",                           abbreviation="DD",   category_id=cat_coag.id,  unit="µg/mL FEU",      ref_max=0.5,  turnaround_hours=4,  price=1800.0),

    # ORINA
    Test(code="OC",    name="Orina completa (EAO)",               abbreviation="OC",   category_id=cat_orina.id, unit="informe",        turnaround_hours=2,  price=500.0),
    Test(code="MICRO", name="Sedimento urinario",                  abbreviation="Sed",  category_id=cat_orina.id, unit="informe",        turnaround_hours=2,  price=400.0),
    Test(code="PROT24",name="Proteinuria 24 hs",                   abbreviation="Prot24",category_id=cat_orina.id,unit="mg/24h",         ref_max=150.0, turnaround_hours=4, price=600.0),
    Test(code="MICRALB",name="Microalbuminuria",                   abbreviation="MAlb", category_id=cat_orina.id, unit="mg/L",           ref_max=30.0,  turnaround_hours=4,  price=900.0),
    Test(code="UROCULT",name="Urocultivo",                         abbreviation="Urocult",category_id=cat_orina.id,unit="UFC/mL",        turnaround_hours=48, price=900.0),

    # HORMONAS
    Test(code="TSH",   name="TSH (hormona tiroestimulante)",       abbreviation="TSH",  category_id=cat_hormo.id, unit="µUI/mL",         ref_min=0.4, ref_max=4.0,   turnaround_hours=4,  price=1200.0),
    Test(code="T4L",   name="T4 libre (tiroxina libre)",           abbreviation="T4L",  category_id=cat_hormo.id, unit="ng/dL",          ref_min=0.8, ref_max=1.8,   turnaround_hours=4,  price=1300.0),
    Test(code="T3L",   name="T3 libre (triyodotironina libre)",    abbreviation="T3L",  category_id=cat_hormo.id, unit="pg/mL",          ref_min=2.3, ref_max=4.2,   turnaround_hours=4,  price=1300.0),
    Test(code="ANTITP",name="Anticuerpos antitiroglobulina",       abbreviation="AntiTg",category_id=cat_hormo.id,unit="UI/mL",          ref_max=115.0, turnaround_hours=24, price=1500.0),
    Test(code="ANTITPO",name="Anticuerpos anti-TPO",              abbreviation="AntiTPO",category_id=cat_hormo.id,unit="UI/mL",         ref_max=34.0,  turnaround_hours=24, price=1500.0),
    Test(code="INSUL", name="Insulina basal",                      abbreviation="Insul",category_id=cat_hormo.id, unit="µUI/mL",         ref_min=2.0, ref_max=25.0,  turnaround_hours=4,  price=1400.0, requires_fasting=True),
    Test(code="CORTSOL",name="Cortisol",                           abbreviation="Cortis",category_id=cat_hormo.id,unit="µg/dL",         ref_range_male="7-25 (AM) / 2-14 (PM)", turnaround_hours=4, price=1300.0),
    Test(code="FSH",   name="FSH (hormona foliculoestimulante)",   abbreviation="FSH",  category_id=cat_hormo.id, unit="mUI/mL",         turnaround_hours=4,  price=1200.0),
    Test(code="LH",    name="LH (hormona luteinizante)",           abbreviation="LH",   category_id=cat_hormo.id, unit="mUI/mL",         turnaround_hours=4,  price=1200.0),
    Test(code="PRL",   name="Prolactina",                          abbreviation="PRL",  category_id=cat_hormo.id, unit="ng/mL",          ref_range_male="2-18", ref_range_female="2-29", ref_min=2, ref_max=29, turnaround_hours=4, price=1200.0),
    Test(code="TESTOS",name="Testosterona total",                  abbreviation="Testo",category_id=cat_hormo.id, unit="ng/dL",          ref_range_male="280-800", ref_range_female="15-70", turnaround_hours=4, price=1400.0),
    Test(code="ESTRA", name="Estradiol",                           abbreviation="E2",   category_id=cat_hormo.id, unit="pg/mL",          turnaround_hours=4,  price=1400.0),
    Test(code="PROGEST",name="Progesterona",                       abbreviation="Prog", category_id=cat_hormo.id, unit="ng/mL",          turnaround_hours=4,  price=1400.0),
    Test(code="BHCG",  name="Beta HCG cuantitativa",              abbreviation="βHCG", category_id=cat_hormo.id, unit="mUI/mL",         turnaround_hours=4,  price=1600.0),
    Test(code="PTH",   name="Paratohormona (PTH)",                 abbreviation="PTH",  category_id=cat_hormo.id, unit="pg/mL",          ref_min=15.0,ref_max=65.0,   turnaround_hours=24, price=2000.0),

    # INMUNOLOGÍA
    Test(code="AGAHBS",name="Antígeno de superficie Hepatitis B (HBsAg)", abbreviation="HBsAg", category_id=cat_inmuno.id, unit="reactivo/no react.", turnaround_hours=4, price=1200.0),
    Test(code="ACHCV", name="Anticuerpos anti-VHC (Hepatitis C)",  abbreviation="Anti-VHC", category_id=cat_inmuno.id, unit="reactivo/no react.", turnaround_hours=4, price=1500.0),
    Test(code="HIV",   name="HIV 1+2 (ELISA 4ª gen.)",            abbreviation="HIV",  category_id=cat_inmuno.id, unit="reactivo/no react.", turnaround_hours=4, price=1500.0),
    Test(code="VDRL",  name="VDRL (sífilis)",                      abbreviation="VDRL", category_id=cat_inmuno.id, unit="reactivo/no react.", turnaround_hours=4, price=600.0),
    Test(code="FAN",   name="Factor antinuclear (FAN/ANA)",        abbreviation="FAN",  category_id=cat_inmuno.id, unit="título",         turnaround_hours=48, price=1800.0),
    Test(code="FR",    name="Factor reumatoide",                   abbreviation="FR",   category_id=cat_inmuno.id, unit="UI/mL",          ref_max=14.0,  turnaround_hours=4,  price=800.0),
    Test(code="PCR_ALTA",name="PCR ultrasensible (hs-CRP)",       abbreviation="hsCRP",category_id=cat_inmuno.id, unit="mg/L",           ref_max=1.0,   turnaround_hours=4,  price=900.0),
    Test(code="IGA",   name="Inmunoglobulina A (IgA)",             abbreviation="IgA",  category_id=cat_inmuno.id, unit="mg/dL",          ref_min=70.0,ref_max=400.0,  turnaround_hours=24, price=800.0),
    Test(code="IGG",   name="Inmunoglobulina G (IgG)",             abbreviation="IgG",  category_id=cat_inmuno.id, unit="mg/dL",          ref_min=700.0,ref_max=1600.0,turnaround_hours=24, price=800.0),
    Test(code="IGE",   name="Inmunoglobulina E (IgE) total",       abbreviation="IgE",  category_id=cat_inmuno.id, unit="UI/mL",          ref_max=100.0, turnaround_hours=24, price=1200.0),
    Test(code="ANTICE",name="Anti-CCP (artritis reumatoidea)",     abbreviation="AntiCCP",category_id=cat_inmuno.id,unit="U/mL",          ref_max=20.0,  turnaround_hours=48, price=2200.0),
    Test(code="PSA",   name="PSA total (próstata)",                abbreviation="PSA",  category_id=cat_inmuno.id, unit="ng/mL",          ref_max=4.0,   turnaround_hours=4,  price=1400.0),
    Test(code="CEA",   name="CEA (antígeno carcinoembrionario)",   abbreviation="CEA",  category_id=cat_inmuno.id, unit="ng/mL",          ref_max=5.0,   turnaround_hours=4,  price=1600.0),
    Test(code="AFP",   name="Alfa-fetoproteína (AFP)",             abbreviation="AFP",  category_id=cat_inmuno.id, unit="ng/mL",          ref_max=10.0,  turnaround_hours=4,  price=1500.0),
    Test(code="CA125", name="CA 125",                              abbreviation="CA125",category_id=cat_inmuno.id, unit="U/mL",           ref_max=35.0,  turnaround_hours=24, price=2000.0),
    Test(code="CA199", name="CA 19-9",                             abbreviation="CA199",category_id=cat_inmuno.id, unit="U/mL",           ref_max=37.0,  turnaround_hours=24, price=2000.0),
    Test(code="TOXO",  name="Toxoplasma IgG/IgM",                  abbreviation="Toxo", category_id=cat_inmuno.id, unit="reactivo/no react.", turnaround_hours=24, price=1200.0),
    Test(code="CHAGAS",name="Chagas (2 técnicas)",                  abbreviation="Chagas",category_id=cat_inmuno.id,unit="reactivo/no react.", turnaround_hours=24, price=1200.0),
    Test(code="BRUCELA",name="Brucelosis (Huddleson/Wright)",      abbreviation="Bruc", category_id=cat_inmuno.id, unit="título",         turnaround_hours=24, price=800.0),

    # MICROBIOLOGÍA
    Test(code="HEMOCULT",name="Hemocultivo (x2)",                  abbreviation="Hemoc",category_id=cat_micro.id,  unit="informe",        turnaround_hours=120, price=1500.0),
    Test(code="COPROCULT",name="Coprocultivo",                      abbreviation="Copro",category_id=cat_micro.id,  unit="informe",        turnaround_hours=72,  price=900.0),
    Test(code="PARSIT",name="Parasitológico de materia fecal",      abbreviation="Parasit",category_id=cat_micro.id,unit="informe",        turnaround_hours=48,  price=600.0),
    Test(code="SECRECULT",name="Cultivo de secreción",              abbreviation="Secrec",category_id=cat_micro.id, unit="informe",        turnaround_hours=72,  price=900.0),
    Test(code="ESPUTO", name="Esputo — cultivo de Koch (BAAR)",     abbreviation="BAAR", category_id=cat_micro.id,  unit="informe",        turnaround_hours=60,  price=700.0),
    Test(code="STREPT", name="Estreptococo β-hemolítico (hisopo)",  abbreviation="Strept",category_id=cat_micro.id, unit="informe",        turnaround_hours=48,  price=600.0),

    # GASES EN SANGRE
    Test(code="GSA",   name="Gases en sangre arterial",             abbreviation="GSA",  category_id=cat_gases.id,  unit="múltiple",       turnaround_hours=1,  price=1200.0),
    Test(code="PH",    name="pH sanguíneo",                         abbreviation="pH",   category_id=cat_gases.id,  unit="unidades",       ref_min=7.35,ref_max=7.45, turnaround_hours=1, price=0.0),
    Test(code="PO2",   name="PO₂ (presión O₂)",                    abbreviation="PO2",  category_id=cat_gases.id,  unit="mmHg",           ref_min=80.0,ref_max=100.0, turnaround_hours=1, price=0.0),
    Test(code="PCO2",  name="PCO₂ (presión CO₂)",                  abbreviation="PCO2", category_id=cat_gases.id,  unit="mmHg",           ref_min=35.0,ref_max=45.0,  turnaround_hours=1, price=0.0),
    Test(code="SAO2",  name="Saturación O₂",                        abbreviation="SaO2", category_id=cat_gases.id,  unit="%",              ref_min=95.0,ref_max=100.0, turnaround_hours=1, price=0.0),
    Test(code="HCO3",  name="Bicarbonato (HCO₃⁻)",                 abbreviation="HCO3", category_id=cat_gases.id,  unit="mEq/L",          ref_min=22.0,ref_max=26.0,  turnaround_hours=1, price=0.0),
]
db.add_all(tests)
db.flush()

# ── Equipos analizadores ──────────────────────────────────────────────────────
equipment = [
    Equipment(name="Sysmex XN-550",   model="XN-550",  manufacturer="Sysmex",      serial_number="SY-XN550-001", equipment_type="Hematología",    location="Sector Hematología", status=EquipmentStatus.ACTIVE, last_calibration=date(2024,10,1), next_calibration=date(2025,4,1)),
    Equipment(name="Cobas c311",       model="c311",    manufacturer="Roche",        serial_number="RC-C311-002",  equipment_type="Bioquímica",     location="Sector Bioquímica",  status=EquipmentStatus.ACTIVE, last_calibration=date(2024,11,1), next_calibration=date(2025,5,1)),
    Equipment(name="Cobas e411",       model="e411",    manufacturer="Roche",        serial_number="RC-E411-003",  equipment_type="Inmunología",    location="Sector Inmunología", status=EquipmentStatus.ACTIVE, last_calibration=date(2024,11,15),next_calibration=date(2025,5,15)),
    Equipment(name="Stago STA-R Max",  model="STA-R",   manufacturer="Stago",        serial_number="ST-STAR-004",  equipment_type="Coagulación",    location="Sector Coagulación", status=EquipmentStatus.ACTIVE, last_calibration=date(2024,9,1),  next_calibration=date(2025,3,1)),
    Equipment(name="Sysmex UC-3500",   model="UC-3500", manufacturer="Sysmex",       serial_number="SY-UC35-005",  equipment_type="Orina",          location="Sector Orina",       status=EquipmentStatus.ACTIVE, last_calibration=date(2024,10,15),next_calibration=date(2025,4,15)),
    Equipment(name="Abbott Alinity h", model="Alinity", manufacturer="Abbott",       serial_number="AB-ALI-006",   equipment_type="Hematología",    location="Guardia/Urgencias",  status=EquipmentStatus.ACTIVE, last_calibration=date(2024,12,1), next_calibration=date(2025,6,1)),
    Equipment(name="Radiometer ABL90", model="ABL90",   manufacturer="Radiometer",   serial_number="RA-ABL90-007", equipment_type="Gases en Sangre",location="UCI",                status=EquipmentStatus.ACTIVE, last_calibration=date(2025,1,1),  next_calibration=date(2025,7,1)),
    Equipment(name="Mindray BC-5390",  model="BC-5390", manufacturer="Mindray",      serial_number="MI-BC53-008",  equipment_type="Hematología",    location="Backup",             status=EquipmentStatus.MAINTENANCE),
]
db.add_all(equipment)
db.flush()

# ── Pacientes demo ────────────────────────────────────────────────────────────
patients = [
    Patient(document_type="DNI", document_number="28456123", last_name="GARCIA",     first_name="Roberto",  birth_date=date(1975,3,15), gender=Gender.M, phone="011-4523-1234", email="roberto.garcia@gmail.com",    health_insurance="OSDE",    insurance_number="OS-12345678", city="Buenos Aires"),
    Patient(document_type="DNI", document_number="34789012", last_name="MARTINEZ",   first_name="Laura",    birth_date=date(1989,7,22), gender=Gender.F, phone="011-4567-8901", email="laura.martinez@hotmail.com",  health_insurance="Swiss Medical", insurance_number="SM-23456789", city="Buenos Aires"),
    Patient(document_type="DNI", document_number="22341678", last_name="RODRIGUEZ",  first_name="Carlos",   birth_date=date(1960,11,8), gender=Gender.M, phone="0341-4234567",  health_insurance="PAMI",            insurance_number="PA-34567890", city="Rosario"),
    Patient(document_type="DNI", document_number="40123456", last_name="FERNANDEZ",  first_name="Valentina",birth_date=date(1998,2,14), gender=Gender.F, phone="0351-4345678",  email="valen.fer@gmail.com",         health_insurance="IOMA",    insurance_number="IO-45678901", city="Córdoba"),
    Patient(document_type="DNI", document_number="18567890", last_name="LOPEZ",      first_name="Antonio",  birth_date=date(1952,9,30), gender=Gender.M, phone="011-4589-2345", health_insurance="PAMI",            insurance_number="PA-56789012", city="Buenos Aires"),
    Patient(document_type="DNI", document_number="31234567", last_name="SANCHEZ",    first_name="María",    birth_date=date(1983,5,18), gender=Gender.F, phone="011-4512-3456", email="maria.sanchez@outlook.com",   health_insurance="Galeno",  insurance_number="GA-67890123", city="La Plata"),
    Patient(document_type="DNI", document_number="37890123", last_name="GONZALEZ",   first_name="Diego",    birth_date=date(1993,12,5), gender=Gender.M, phone="011-4578-9012", email="diego.gonza@gmail.com",       health_insurance="Medicus", insurance_number="ME-78901234", city="Buenos Aires"),
    Patient(document_type="DNI", document_number="25678901", last_name="DIAZ",       first_name="Susana",   birth_date=date(1968,4,27), gender=Gender.F, phone="0261-4456789",  health_insurance="OSDE",            insurance_number="OS-89012345", city="Mendoza"),
    Patient(document_type="DNI", document_number="43210987", last_name="MORENO",     first_name="Lucas",    birth_date=date(2001,8,19), gender=Gender.M, phone="011-4534-6789", email="lucas.moreno@gmail.com",      health_insurance="Sancor Salud", city="Buenos Aires"),
    Patient(document_type="DNI", document_number="29876543", last_name="RUIZ",       first_name="Ana Clara",birth_date=date(1978,1,11), gender=Gender.F, phone="0381-4523456",  email="anaclara.ruiz@gmail.com",     health_insurance="Swiss Medical", insurance_number="SM-90123456", city="San Miguel de Tucumán"),
]
db.add_all(patients)
db.flush()

# ── Órdenes y resultados demo ─────────────────────────────────────────────────
def make_order(pat, doc, urgency, days_ago, test_codes, results_values=None):
    order_date = datetime.now() - timedelta(days=days_ago, hours=random.randint(0,8))
    num = order_date.strftime("%Y%m%d") + str(random.randint(1000,9999))
    order = Order(
        order_number=num, patient_id=pat.id,
        doctor_id=doc.id if doc else None,
        urgency=urgency, order_date=order_date,
        status=OrderStatus.PENDING,
        created_by_id=users[0].id
    )
    db.add(order); db.flush()

    test_map = {t.code: t for t in tests}
    total = 0.0
    for code in test_codes:
        t = test_map.get(code)
        if not t: continue
        item = OrderItem(order_id=order.id, test_id=t.id, status=OrderItemStatus.PENDING)
        db.add(item); db.flush(); total += t.price or 0

        if results_values and code in results_values:
            val = str(results_values[code])
            is_abn, flag = False, ""
            try:
                v = float(val)
                if t.ref_max and v > t.ref_max: is_abn, flag = True, "H"
                elif t.ref_min and v < t.ref_min: is_abn, flag = True, "L"
            except: pass
            eq = equipment[0] if "HEMA" in t.category.code else (equipment[1] if "BIOQ" in t.category.code else equipment[2])
            result = Result(
                order_item_id=item.id, equipment_id=eq.id,
                value=val, unit=t.unit, numeric_value=float(val) if val.replace('.','').isdigit() else None,
                status=ResultStatus.VALIDATED, is_abnormal=is_abn, abnormal_flag=flag or None,
                validated_by_id=users[1].id, validated_at=order_date + timedelta(hours=2),
                result_date=order_date + timedelta(hours=1),
            )
            db.add(result)
            item.status = OrderItemStatus.VALIDATED

    order.total_price = total
    if all(i.status == OrderItemStatus.VALIDATED for i in order.items):
        order.status = OrderStatus.VALIDATED
    elif any(i.status in [OrderItemStatus.RESULTED, OrderItemStatus.VALIDATED] for i in order.items):
        order.status = OrderStatus.IN_PROGRESS
    return order

# Órdenes con resultados validados (histórico 30 días)
make_order(patients[0], doctors[0], Urgency.ROUTINE, 28, ["GLU","COL","HDL","LDL","TRG","TGO","TGP","CREA","UREA"], {"GLU":"95","COL":"215","HDL":"38","LDL":"145","TRG":"180","TGO":"32","TGP":"28","CREA":"1.1","UREA":"38"})
make_order(patients[1], doctors[2], Urgency.ROUTINE, 25, ["TSH","T4L","T3L"], {"TSH":"6.8","T4L":"0.7","T3L":"2.1"})
make_order(patients[2], doctors[0], Urgency.URGENT,  20, ["HMG","VSG","PCR","FIBRI","KPTT","TP"], {"HMG":"ver informe","VSG":"45","PCR":"32","FIBRI":"380","KPTT":"28","TP":"13"})
make_order(patients[3], doctors[3], Urgency.ROUTINE, 18, ["BHCG","HMG","FERR","FOLATO","B12"], {"BHCG":"0.5","HMG":"ver informe","FERR":"8","FOLATO":"2.8","B12":"185"})
make_order(patients[4], doctors[4], Urgency.ROUTINE, 15, ["CREA","UREA","NA","K","CL","CA","MICRALB","OC"], {"CREA":"2.1","UREA":"68","NA":"138","K":"5.4","CL":"101","CA":"9.2","MICRALB":"65","OC":"ver informe"})
make_order(patients[5], doctors[5], Urgency.ROUTINE, 12, ["FAN","FR","ANTICE","PCR","VSG"], {"FAN":"1/320","FR":"28","ANTICE":"45","PCR":"18","VSG":"52"})
make_order(patients[6], doctors[1], Urgency.STAT,     8, ["GSA","PH","PO2","PCO2","SAO2","HCO3","HMG","KPTT","TP"], {"PH":"7.32","PO2":"72","PCO2":"48","SAO2":"93","HCO3":"20","HMG":"ver informe","KPTT":"42","TP":"15"})
make_order(patients[7], doctors[0], Urgency.ROUTINE,  5, ["GLU","HBA1C","INSUL","COL","HDL","LDL","TRG","VITD"], {"GLU":"128","HBA1C":"7.2","INSUL":"18","COL":"198","HDL":"42","LDL":"120","TRG":"180","VITD":"18"})
make_order(patients[8], doctors[3], Urgency.ROUTINE,  3, ["HMG","FERR","FE","TIBC","B12","FOLATO"], {"HMG":"ver informe","FERR":"6","FE":"45","TIBC":"420","B12":"195","FOLATO":"2.1"})

# Órdenes pendientes (hoy)
make_order(patients[9], doctors[0], Urgency.ROUTINE, 0, ["GLU","COL","HDL","LDL","TRG","TGO","TGP","GGT","FAL","BT","CREA","UREA","ACUR"])
make_order(patients[0], doctors[2], Urgency.URGENT,  0, ["TSH","T4L","ANTITPO","CORTSOL"])
make_order(patients[2], doctors[4], Urgency.STAT,    0, ["GSA","HMG","CREA","NA","K"])

db.commit()
print("✅ Seed completado:")
print(f"   - {db.query(User).count()} usuarios")
print(f"   - {db.query(Doctor).count()} médicos")
print(f"   - {db.query(TestCategory).count()} categorías")
print(f"   - {db.query(Test).count()} análisis del nomenclador")
print(f"   - {db.query(Equipment).count()} equipos")
print(f"   - {db.query(Patient).count()} pacientes")
print(f"   - {db.query(Order).count()} órdenes")
print(f"   - {db.query(Result).count()} resultados")
print("\n🔑 Login: admin / admin123")
db.close()
