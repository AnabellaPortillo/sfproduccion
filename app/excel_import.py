"""
Importador de Excel para LabCore LIS.

Formato esperado por hoja (una hoja = un protocolo):
  Fila 1 : Protocolo: [nro]   Fecha: [dd/mm/yyyy]   Urgencia: [ROUTINE|URGENT|STAT]
  Fila 2 : Apellido: [texto]  Nombre: [texto]
  Fila 3 : DNI: [nro]         Fecha Nac.: [dd/mm/yyyy]   Género: [M|F|O]
  Fila 4 : Médico: [texto]    Obra Social: [texto]   N° Afiliado: [texto]
  Fila 5 : Observaciones: [texto]
  Fila 6 : (encabezados) ANÁLISIS | RESULTADO | UNIDAD | REFERENCIA | OBSERVACIONES
  Fila 7+: [nombre o código análisis] | [valor] | [unidad] | [ref] | [obs]

El importador también acepta columnas en inglés (TEST/CODE | RESULT | UNIT).
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

import openpyxl
from openpyxl.workbook import Workbook


# ── Resultado de una determinación ───────────────────────────────────────────

@dataclass
class ImportedResult:
    test_name: str         # nombre o código tal como viene en el Excel
    value: str
    unit: str = ""
    reference: str = ""
    observations: str = ""


# ── Datos de un protocolo (una hoja) ─────────────────────────────────────────

@dataclass
class ImportedProtocol:
    sheet_name: str
    protocol_number: str = ""
    order_date: Optional[date] = None
    urgency: str = "ROUTINE"
    # Paciente
    last_name: str = ""
    first_name: str = ""
    document_number: str = ""
    birth_date: Optional[date] = None
    gender: str = "M"
    health_insurance: str = ""
    insurance_number: str = ""
    # Médico (texto libre — se buscará o creará)
    doctor_name: str = ""
    observations: str = ""
    # Resultados
    results: list[ImportedResult] = field(default_factory=list)
    # Errores de parseo no fatales
    warnings: list[str] = field(default_factory=list)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cell(ws, row: int, col: int) -> str:
    """Devuelve el valor de una celda como string, vacío si None."""
    v = ws.cell(row=row, column=col).value
    return str(v).strip() if v is not None else ""


def _find_value(ws, row: int, key: str) -> str:
    """
    Recorre todas las columnas de una fila buscando una celda cuyo valor
    comience con 'key:' y devuelve lo que sigue (en la misma celda o en la siguiente).
    """
    key_lower = key.lower().rstrip(":")
    for col in range(1, ws.max_column + 2):
        raw = _cell(ws, row, col)
        if raw.lower().startswith(key_lower):
            # valor puede estar en la misma celda después de ':'
            after = re.split(r":\s*", raw, maxsplit=1)
            if len(after) > 1 and after[1]:
                return after[1].strip()
            # o en la celda siguiente
            nxt = _cell(ws, row, col + 1)
            return nxt
    return ""


def _parse_date(s: str) -> Optional[date]:
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    # openpyxl puede devolver un datetime directamente
    return None


def _parse_urgency(s: str) -> str:
    s = s.upper()
    if "STAT" in s:
        return "STAT"
    if "URG" in s:
        return "URGENT"
    return "ROUTINE"


def _parse_gender(s: str) -> str:
    s = s.strip().upper()
    if s in ("F", "FEM", "FEMENINO", "FEMALE"):
        return "F"
    if s in ("O", "OTRO", "OTHER", "X"):
        return "O"
    return "M"


def _find_header_row(ws) -> int:
    """
    Detecta la fila de encabezados de resultados buscando palabras clave
    como ANÁLISIS, RESULTADO, TEST, RESULT, CÓDIGO, etc.
    """
    keywords = {"análisis", "analisis", "test", "código", "codigo", "code",
                "examen", "determinacion", "determinación"}
    for row in range(1, min(20, ws.max_row + 1)):
        for col in range(1, ws.max_column + 1):
            cell_val = _cell(ws, row, col).lower()
            if any(kw in cell_val for kw in keywords):
                return row
    return 6  # fallback


def _col_index(header_row_values: list[str], *candidates: str) -> int:
    """Retorna el índice (1-based) de la primera columna que coincida."""
    candidates_lower = [c.lower() for c in candidates]
    for idx, h in enumerate(header_row_values, start=1):
        if h.lower().strip() in candidates_lower:
            return idx
    return 0


# ── Parser principal ──────────────────────────────────────────────────────────

def _scan_field(ws, *keys: str, max_row: int = 12) -> str:
    """Busca una clave en cualquier fila dentro de las primeras max_row filas."""
    for row in range(1, max_row + 1):
        for key in keys:
            val = _find_value(ws, row, key)
            if val:
                return val
    return ""


def parse_sheet(ws) -> ImportedProtocol:
    proto = ImportedProtocol(sheet_name=ws.title)

    # ── Búsqueda flexible en las primeras filas ───────────────────────────────
    proto.protocol_number = _scan_field(ws, "protocolo", "protocol", "n° protocolo")
    raw_date  = _scan_field(ws, "fecha", "date")
    proto.order_date = _parse_date(raw_date)
    proto.urgency = _parse_urgency(_scan_field(ws, "urgencia", "urgency") or "ROUTINE")

    proto.last_name   = _scan_field(ws, "apellido", "last name", "lastname").upper()
    proto.first_name  = _scan_field(ws, "nombre", "first name", "name")

    proto.document_number = _scan_field(ws, "dni", "documento", "document", "nro doc", "n° doc")
    raw_birth = _scan_field(ws, "fecha nac", "nacimiento", "birth", "fecha de nacimiento")
    proto.birth_date  = _parse_date(raw_birth)
    proto.gender      = _parse_gender(_scan_field(ws, "género", "genero", "gender", "sexo") or "M")

    proto.doctor_name     = _scan_field(ws, "médico", "medico", "doctor", "profesional")
    proto.health_insurance = _scan_field(ws, "obra social", "cobertura", "insurance", "prepaga")
    proto.insurance_number = _scan_field(ws, "n° afiliado", "afiliado", "nro afiliado", "member")
    proto.observations     = _scan_field(ws, "observaciones", "observations", "obs")

    # Validaciones básicas
    if not proto.last_name and not proto.document_number:
        proto.warnings.append("No se encontró apellido ni documento del paciente.")
    if not proto.birth_date:
        proto.warnings.append("No se encontró fecha de nacimiento — se usará 01/01/1900.")
        proto.birth_date = date(1900, 1, 1)

    # ── Filas de resultados ───────────────────────────────────────────────────
    hdr_row = _find_header_row(ws)
    headers = [_cell(ws, hdr_row, c) for c in range(1, ws.max_column + 1)]

    col_test = _col_index(headers, "análisis", "analisis", "test", "código", "codigo",
                          "code", "examen", "determinacion", "determinación")
    col_result = _col_index(headers, "resultado", "result", "valor", "value")
    col_unit   = _col_index(headers, "unidad", "unit", "u.m.", "um")
    col_ref    = _col_index(headers, "referencia", "reference", "ref", "valor referencia")
    col_obs    = _col_index(headers, "observaciones", "observations", "obs", "nota", "notas")

    if col_test == 0:
        proto.warnings.append(f"No se encontró columna de análisis en fila {hdr_row}. "
                               "Verifique que exista una columna llamada 'Análisis' o 'Test'.")
        return proto

    for row in range(hdr_row + 1, ws.max_row + 1):
        test_name = _cell(ws, row, col_test)
        if not test_name:
            continue  # fila vacía, ignorar
        value     = _cell(ws, row, col_result) if col_result else ""
        unit      = _cell(ws, row, col_unit)   if col_unit   else ""
        reference = _cell(ws, row, col_ref)    if col_ref    else ""
        obs       = _cell(ws, row, col_obs)    if col_obs    else ""
        proto.results.append(ImportedResult(
            test_name=test_name, value=value,
            unit=unit, reference=reference, observations=obs
        ))

    return proto


def parse_workbook(filepath: str) -> list[ImportedProtocol]:
    """Lee todas las hojas de un .xlsx y retorna una lista de ImportedProtocol."""
    wb = openpyxl.load_workbook(filepath, data_only=True)
    return [parse_sheet(wb[name]) for name in wb.sheetnames]


# ── Generador de template ─────────────────────────────────────────────────────

def generate_template(filepath: str, test_codes: list[dict] | None = None):
    """
    Genera un archivo .xlsx de ejemplo con 2 hojas-protocolo rellenas.
    test_codes: lista de dicts con 'name' y 'code' del catálogo.
    """
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()

    BLUE   = "1e40af"
    LBLUE  = "dbeafe"
    GRAY   = "f1f5f9"
    GREEN  = "166534"
    LGREEN = "dcfce7"

    header_font  = Font(bold=True, color="FFFFFF", size=10)
    header_fill  = PatternFill("solid", fgColor=BLUE)
    section_fill = PatternFill("solid", fgColor=LBLUE)
    section_font = Font(bold=True, color=BLUE, size=9)
    result_fill  = PatternFill("solid", fgColor=GRAY)
    col_header_fill = PatternFill("solid", fgColor=GREEN)
    col_header_font = Font(bold=True, color="FFFFFF", size=9)
    thin_border  = Border(
        left=Side(style="thin", color="cbd5e1"),
        right=Side(style="thin", color="cbd5e1"),
        top=Side(style="thin", color="cbd5e1"),
        bottom=Side(style="thin", color="cbd5e1"),
    )

    demo_tests = test_codes or [
        {"name": "Glucemia",          "code": "GLU"},
        {"name": "Colesterol total",  "code": "COL"},
        {"name": "Hemoglobina",       "code": "HB"},
        {"name": "Creatinina",        "code": "CREA"},
        {"name": "TSH",               "code": "TSH"},
    ]

    for sheet_idx, (last, first, dni, bdate, gender, doc, ins, prot, fecha) in enumerate([
        ("GARCIA",    "Roberto",  "28456123", "15/03/1975", "M", "Dr. Rodriguez",   "OSDE",          "010526001", "01/05/2026"),
        ("MARTINEZ",  "Laura",    "34789012", "22/07/1989", "F", "Dra. Martinez",    "Swiss Medical", "010526002", "01/05/2026"),
    ], start=1):
        ws = wb.active if sheet_idx == 1 else wb.create_sheet()
        ws.title = prot

        # Anchos de columna
        for col, width in [(1,22),(2,18),(3,22),(4,18),(5,22),(6,20)]:
            ws.column_dimensions[get_column_letter(col)].width = width

        def labeled(row, col, label, value="", label_fill=section_fill, val_fill=None):
            lc = ws.cell(row=row, column=col, value=label)
            lc.font = section_font; lc.fill = label_fill; lc.border = thin_border
            lc.alignment = Alignment(horizontal="right", vertical="center")
            vc = ws.cell(row=row, column=col+1, value=value)
            if val_fill: vc.fill = val_fill
            vc.border = thin_border
            vc.alignment = Alignment(vertical="center")

        # Título
        ws.merge_cells("A1:F1")
        title = ws["A1"]
        title.value = "LabCore LIS — Importación de Protocolo"
        title.font = Font(bold=True, color="FFFFFF", size=12)
        title.fill = PatternFill("solid", fgColor="0f172a")
        title.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 24

        # Fila 2 — identificación orden
        labeled(2, 1, "Protocolo:", prot)
        labeled(2, 3, "Fecha:", fecha)
        labeled(2, 5, "Urgencia:", "ROUTINE")

        # Fila 3 — paciente nombre
        labeled(3, 1, "Apellido:", last)
        labeled(3, 3, "Nombre:", first)

        # Fila 4 — paciente datos
        labeled(4, 1, "DNI:", dni)
        labeled(4, 3, "Fecha Nac.:", bdate)
        labeled(4, 5, "Género:", gender)

        # Fila 5 — médico y cobertura
        labeled(5, 1, "Médico:", doc)
        labeled(5, 3, "Obra Social:", ins)
        labeled(5, 5, "N° Afiliado:", f"OS-{dni[:5]}")

        # Fila 6 — observaciones
        labeled(6, 1, "Observaciones:", "Paciente en ayunas")
        ws.row_dimensions[6].height = 16

        # Fila 7 — encabezados de resultados
        headers = ["Análisis", "Código", "Resultado", "Unidad", "Referencia", "Observaciones"]
        for ci, h in enumerate(headers, 1):
            cell = ws.cell(row=7, column=ci, value=h)
            cell.font = col_header_font
            cell.fill = col_header_fill
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[7].height = 18

        # Filas de resultados demo
        sample_values = ["95", "215", "14.2", "1.1", "2.8"]
        sample_units  = ["mg/dL","mg/dL","g/dL","mg/dL","µUI/mL"]
        sample_refs   = ["70-100","<200","13.5-17.5","0.7-1.2","0.4-4.0"]
        for ri, t in enumerate(demo_tests):
            row = 8 + ri
            fill = PatternFill("solid", fgColor=("ffffff" if ri % 2 == 0 else "f8fafc"))
            data = [t["name"], t["code"],
                    sample_values[ri] if ri < len(sample_values) else "",
                    sample_units[ri]  if ri < len(sample_units)  else "",
                    sample_refs[ri]   if ri < len(sample_refs)   else "",
                    ""]
            for ci, val in enumerate(data, 1):
                cell = ws.cell(row=row, column=ci, value=val)
                cell.fill = fill
                cell.border = thin_border
                cell.alignment = Alignment(vertical="center")

        # Agregar más filas vacías para que el usuario llene
        for extra in range(len(demo_tests), len(demo_tests) + 10):
            row = 8 + extra
            fill = PatternFill("solid", fgColor=("ffffff" if extra % 2 == 0 else "f8fafc"))
            for ci in range(1, 7):
                ws.cell(row=row, column=ci).fill = fill
                ws.cell(row=row, column=ci).border = thin_border

        # Freeze panes
        ws.freeze_panes = "A8"

    # Hoja de instrucciones
    ws_help = wb.create_sheet("INSTRUCCIONES", 0)
    ws_help.column_dimensions["A"].width = 80
    instrucciones = [
        ("LabCore LIS — Instrucciones de importación", True, "0f172a", "FFFFFF", 14),
        ("", False, None, None, 11),
        ("ESTRUCTURA DE CADA HOJA:", True, "1e40af", "FFFFFF", 11),
        ("  • Cada hoja del archivo representa un PROTOCOLO (orden de análisis).", False, None, None, 10),
        ("  • El nombre de la hoja puede ser el número de protocolo u otro identificador.", False, None, None, 10),
        ("", False, None, None, 10),
        ("FILAS DE CABECERA (filas 2 a 6):", True, "1e40af", "FFFFFF", 11),
        ("  Fila 2:  Protocolo: [nro]    Fecha: [dd/mm/yyyy]    Urgencia: [ROUTINE | URGENT | STAT]", False, None, None, 10),
        ("  Fila 3:  Apellido: [apellido]    Nombre: [nombre]", False, None, None, 10),
        ("  Fila 4:  DNI: [número]    Fecha Nac.: [dd/mm/yyyy]    Género: [M | F | O]", False, None, None, 10),
        ("  Fila 5:  Médico: [nombre]    Obra Social: [nombre]    N° Afiliado: [número]", False, None, None, 10),
        ("  Fila 6:  Observaciones: [texto libre]", False, None, None, 10),
        ("", False, None, None, 10),
        ("RESULTADOS (fila 7 en adelante):", True, "1e40af", "FFFFFF", 11),
        ("  Fila 7:  ENCABEZADOS — deben incluir las columnas:", False, None, None, 10),
        ("           Análisis | Código | Resultado | Unidad | Referencia | Observaciones", False, None, None, 10),
        ("  Fila 8+: Un resultado por fila. El campo 'Análisis' o 'Código' se usará para", False, None, None, 10),
        ("           buscar el análisis en el catálogo del sistema.", False, None, None, 10),
        ("", False, None, None, 10),
        ("NOTAS:", True, "166534", "FFFFFF", 11),
        ("  ✓ Si el paciente ya existe (mismo DNI), se usarán sus datos existentes.", False, None, None, 10),
        ("  ✓ Si el análisis no se encuentra en el catálogo, se importa de todas formas con", False, None, None, 10),
        ("    el nombre tal cual está en el Excel, marcado para revisión.", False, None, None, 10),
        ("  ✓ El sistema detecta automáticamente valores fuera de rango.", False, None, None, 10),
        ("  ✓ Los protocolos importados quedan con estado 'VALIDADO'.", False, None, None, 10),
        ("  ✓ Las hojas en blanco o la hoja 'INSTRUCCIONES' se omiten.", False, None, None, 10),
    ]
    for ri, (text, bold, bg, fg, size) in enumerate(instrucciones, 1):
        cell = ws_help.cell(row=ri, column=1, value=text)
        cell.font = Font(bold=bold, size=size, color=fg or "000000")
        if bg:
            cell.fill = PatternFill("solid", fgColor=bg)
        ws_help.row_dimensions[ri].height = 18

    wb.save(filepath)
