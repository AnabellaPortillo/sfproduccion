# LabCore LIS — Sistema de Información de Laboratorio Clínico

Sistema web completo para gestión de análisis clínicos, similar a LabCore / LabWare.

## Módulos

| Módulo | Descripción |
|---|---|
| **Pacientes** | Alta, edición, búsqueda, historial de órdenes |
| **Órdenes** | Creación con múltiples análisis, urgencia, médico solicitante |
| **Resultados** | Carga por equipo, detección automática de valores fuera de rango, validación |
| **Catálogo** | Análisis del nomenclador nacional argentino con rangos de referencia |
| **Equipos** | Gestión de analizadores, estado, calibraciones |
| **Estadísticas** | Dashboard con KPIs, tendencias, distribución por categoría, tasa de anormalidad |
| **Administración** | Usuarios con roles, médicos |

## Instalación y arranque

```bash
pip install -r requirements.txt
python seed.py        # carga datos del nomenclador + demo
uvicorn app.main:app --reload --port 8000
```

O simplemente:

```bash
bash run.sh
```

Abrir: http://localhost:8000  
Usuario demo: **admin / admin123**

## Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Bootstrap 5 + Chart.js + DataTables
- **Auth**: Sesiones con middleware Starlette

## Análisis incluidos (nomenclador nacional)

- Hematología: hemograma, VSG, reticulocitos, frotis
- Bioquímica: glucemia, HbA1c, perfil lipídico, función hepática, función renal, electrolitos, hierro, vitaminas
- Coagulación: KPTT, TP/INR, fibrinógeno, dímero D
- Orina: EAO, sedimento, proteinuria 24h, microalbuminuria, urocultivo
- Hormonas: TSH, T4L, T3L, insulina, cortisol, FSH, LH, prolactina, testosterona, estradiol, β-HCG, PTH
- Inmunología: hepatitis B/C, HIV, VDRL, FAN, factor reumatoide, anti-CCP, PSA, CEA, AFP, CA125, CA19-9, Chagas, toxoplasma
- Microbiología: hemocultivo, coprocultivo, urocultivo, BAAR
- Gases en sangre: pH, PO₂, PCO₂, SaO₂, HCO₃⁻
