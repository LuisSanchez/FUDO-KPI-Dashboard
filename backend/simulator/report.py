"""
PDF financial report generator for the FUDO Analytics simulator.

Entry point: build_financial_report(df_sales, df_expenses, month=None) -> bytes
"""

import io
import math
import datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .data_processing import (
    get_sales_table,
    get_product_prices_table,
    kpi_calculations,
)

# ── Colors ────────────────────────────────────────────────────────────────────
ORANGE = colors.HexColor("#F97316")
DARK_BG = colors.HexColor("#0F172A")
CARD_BG = colors.HexColor("#1E293B")
BORDER = colors.HexColor("#334155")
TEXT = colors.HexColor("#F1F5F9")
SUBTEXT = colors.HexColor("#94A3B8")
RED = colors.HexColor("#EF4444")
GREEN = colors.HexColor("#22C55E")
YELLOW = colors.HexColor("#EAB308")
WHITE = colors.white

PAGE_W, PAGE_H = A4
W = PAGE_W - 3 * cm


# ── Style helpers ─────────────────────────────────────────────────────────────
_SS = getSampleStyleSheet()


def _s(name, **kw):
    return ParagraphStyle(name, parent=_SS["Normal"], **kw)


ST = {
    "cover_title": _s(
        "ct",
        fontSize=24,
        textColor=WHITE,
        fontName="Helvetica-Bold",
        leading=30,
        alignment=TA_CENTER,
    ),
    "cover_sub": _s(
        "cs",
        fontSize=12,
        textColor=ORANGE,
        fontName="Helvetica",
        leading=16,
        alignment=TA_CENTER,
    ),
    "cover_meta": _s(
        "cm",
        fontSize=9,
        textColor=SUBTEXT,
        fontName="Helvetica",
        leading=14,
        alignment=TA_CENTER,
    ),
    "section": _s(
        "sc",
        fontSize=12,
        textColor=ORANGE,
        fontName="Helvetica-Bold",
        leading=16,
        spaceBefore=14,
        spaceAfter=4,
    ),
    "body": _s("bd", fontSize=9, textColor=TEXT, fontName="Helvetica", leading=14),
    "bodysub": _s(
        "bs", fontSize=8.5, textColor=SUBTEXT, fontName="Helvetica", leading=13
    ),
    "info": _s(
        "if",
        fontSize=9,
        textColor=colors.HexColor("#7DD3FC"),
        fontName="Helvetica",
        leading=13,
        leftIndent=8,
        rightIndent=8,
        borderColor=colors.HexColor("#0369A1"),
        borderWidth=0.5,
        borderPadding=6,
        backColor=colors.HexColor("#001829"),
    ),
    "footer": _s(
        "ft",
        fontSize=7,
        textColor=SUBTEXT,
        fontName="Helvetica",
        leading=10,
        alignment=TA_CENTER,
    ),
}

BASE_TABLE_STYLE = [
    ("BACKGROUND", (0, 0), (-1, 0), CARD_BG),
    ("TEXTCOLOR", (0, 0), (-1, 0), ORANGE),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 8),
    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
    ("TOPPADDING", (0, 0), (-1, 0), 6),
    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 1), (-1, -1), 8),
    ("TEXTCOLOR", (0, 1), (-1, -1), TEXT),
    ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
    ("TOPPADDING", (0, 1), (-1, -1), 4),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [DARK_BG, CARD_BG]),
    ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
]


def _P(text, style="body"):
    return Paragraph(text, ST[style] if isinstance(style, str) else style)


def _HR(color=BORDER, t=0.5, sp=4):
    return HRFlowable(
        width="100%", thickness=t, color=color, spaceAfter=sp, spaceBefore=sp
    )


def _clp(n):
    return "$" + f"{abs(int(n)):,}".replace(",", ".")


def _tbl(data, col_widths, extra_style=None):
    style = list(BASE_TABLE_STYLE)
    if extra_style:
        style.extend(extra_style)
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle(style))
    return t


# ── KPI summary card ──────────────────────────────────────────────────────────


def _kpi_summary_table(kpis):
    ing = kpis["ingresos"]
    gas = kpis["gastos"]
    ebt = kpis["ebitda"]

    ebitda_val = ebt["ebitda"]
    ebitda_pct = ebt["ebitda_percentage"]
    ebitda_color = GREEN if ebitda_val >= 0 else RED

    rows = [
        ["Concepto", "Valor", "Detalle"],
        [
            "Ingresos (sin IVA)",
            _clp(ing["total_ingreso_sin_iva"]),
            f"con IVA: {_clp(ing['total_ingreso'])}",
        ],
        [
            "  Comisiones Uber Eats",
            f"− {_clp(ing['comision_total'])}",
            "30% sobre ventas Uber",
        ],
        [
            "  CMV (ingredientes)",
            f"{ing['cmv_percentage']:.1f}%",
            _clp(ing["cmv"]),
        ],
        [
            "  Margen bruto FUDO",
            (
                f"{(ing['total_margen_sin_iva'] / ing['total_ingreso_sin_iva'] * 100):.1f}%"
                if ing["total_ingreso_sin_iva"]
                else "—"
            ),
            _clp(ing["total_margen_sin_iva"]),
        ],
        ["Gastos operacionales", _clp(gas["gastos_totales"]), ""],
        [
            "  Pagado",
            _clp(gas["pagados_totales"]),
            f"Por pagar: {_clp(gas['por_pagar_totales'])}",
        ],
        [
            "EBITDA",
            f"{_clp(ebitda_val)}",
            f"{ebitda_pct:.1f}%",
        ],
    ]
    if gas["prestamos_socios"] > 0:
        rows.insert(
            -1, ["  Préstamos (excl.)", _clp(gas["prestamos_socios"]), "No operacional"]
        )
    if gas["activo_fijo"] > 0:
        rows.insert(-1, ["  Activo fijo (excl.)", _clp(gas["activo_fijo"]), "CapEx"])

    extra = [
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, -1), (2, -1), ebitda_color),
        ("BACKGROUND", (0, -1), (-1, -1), CARD_BG),
    ]
    return _tbl(rows, [W * 0.42, W * 0.28, W * 0.30], extra)


# ── Sales by product table ─────────────────────────────────────────────────────


def _sales_table(df_sales):
    rows_data = get_sales_table(df_sales)
    if not rows_data:
        return _P("Sin datos de ventas.", "bodysub")

    rows = [["Producto", "Cant.", "Ingreso s/IVA", "CMV%", "Margen%"]]
    for r in rows_data[:20]:  # cap at 20 rows
        rows.append(
            [
                r["Producto"][:38],
                str(int(r["cantidad"])),
                _clp(r["ingreso_sin_iva"]),
                f"{r['cmv_pct']:.1f}%",
                f"{r['margen_pct']:.1f}%",
            ]
        )

    return _tbl(rows, [W * 0.44, W * 0.08, W * 0.20, W * 0.14, W * 0.14])


# ── Break-even analysis ────────────────────────────────────────────────────────


def _breakeven_section(kpis, df_sales):
    ing = kpis["ingresos"]
    gas = kpis["gastos"]
    ebt = kpis["ebitda"]

    total_ingreso = ing["total_ingreso_sin_iva"]
    total_gastos = gas["gastos_totales"]
    ebitda = ebt["ebitda"]

    # Aggregate per-unit averages across all products
    if df_sales.empty or total_ingreso == 0:
        return _P("Datos insuficientes para análisis de break-even.", "bodysub")

    total_units = df_sales["Cantidad"].sum()
    if total_units == 0:
        return _P("Sin unidades vendidas.", "bodysub")

    avg_ingreso_per_unit = total_ingreso / total_units
    avg_margen_per_unit = ing["total_margen_sin_iva"] / total_units

    # Break-even: ebitda + x*m = 0  →  x = -ebitda / m
    if ebitda >= 0:
        be_units_needed = 0
        be_units_total = int(total_units)
        be_note = "Ya alcanzado"
    elif avg_margen_per_unit > 0:
        be_units_needed = math.ceil(-ebitda / avg_margen_per_unit)
        be_units_total = int(total_units) + be_units_needed
        be_note = ""
    else:
        return _P(
            "El margen por unidad es negativo. Revisar precios y costos.", "bodysub"
        )

    # 25% EBITDA: x = (0.25*I - ebitda) / (m - 0.25*i)
    denom_25 = avg_margen_per_unit - 0.25 * avg_ingreso_per_unit
    if ebt["ebitda_percentage"] >= 25:
        t25_units_needed = 0
        t25_units_total = int(total_units)
        t25_note = "Ya alcanzado"
    elif denom_25 > 0:
        numer_25 = 0.25 * total_ingreso - ebitda
        t25_units_needed = math.ceil(numer_25 / denom_25)
        t25_units_total = int(total_units) + t25_units_needed
        t25_note = ""
    else:
        t25_units_needed = None
        t25_units_total = None
        t25_note = "Margen insuficiente"

    # Revenue projections (sin IVA → con IVA)
    def _proj(units):
        return units * avg_ingreso_per_unit if units else None

    be_ingreso = _proj(be_units_total)
    t25_ingreso = _proj(t25_units_total)

    rows = [
        ["Métrica", "Unidades", "Ingreso s/IVA", "Ingreso c/IVA", "Nota"],
        [
            "Situación actual",
            f"{int(total_units):,}",
            _clp(total_ingreso),
            _clp(total_ingreso * 1.19),
            f"EBITDA {ebt['ebitda_percentage']:.1f}%",
        ],
        [
            "Break-even (EBITDA = 0)",
            f"+{be_units_needed:,}" if be_units_needed else "—",
            _clp(be_ingreso) if be_ingreso else "—",
            _clp(be_ingreso * 1.19) if be_ingreso else "—",
            be_note,
        ],
        [
            "EBITDA 25%",
            f"+{t25_units_needed:,}" if t25_units_needed else "—",
            _clp(t25_ingreso) if t25_ingreso else "—",
            _clp(t25_ingreso * 1.19) if t25_ingreso else "—",
            t25_note,
        ],
    ]

    extra = [
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 2), (-1, 2), YELLOW),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 3), (-1, 3), GREEN),
    ]
    return _tbl(rows, [W * 0.30, W * 0.14, W * 0.18, W * 0.18, W * 0.20], extra)


# ── Main builder ──────────────────────────────────────────────────────────────


def build_financial_report(
    df_sales: pd.DataFrame,
    df_expenses: pd.DataFrame,
    month: str | None = None,
) -> bytes:
    """
    Build a PDF financial report and return the bytes.

    Parameters
    ----------
    df_sales    : cleaned sales DataFrame (output of sales_clean_up_data)
    df_expenses : raw expenses DataFrame (as stored in session)
    month       : optional "YYYY-MM" string to filter by month

    Returns
    -------
    bytes — PDF content ready to send as HTTP response
    """
    df = df_sales.copy()
    if month:
        df = df[df["created_at"].dt.to_period("M").astype(str) == month]

    kpis = kpi_calculations(df, df_expenses)

    month_label = month or "Todos los meses"
    generated_at = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    story = []

    # ── Cover ──────────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 0.5 * cm),
        _P("FUDO Analytics", "cover_title"),
        Spacer(1, 0.3 * cm),
        _P("Reporte Financiero — Oh My Pizza", "cover_sub"),
        Spacer(1, 0.2 * cm),
        _P(f"Período: {month_label}  ·  Generado: {generated_at}", "cover_meta"),
        Spacer(1, 0.4 * cm),
        _HR(ORANGE, t=1),
        Spacer(1, 0.4 * cm),
    ]

    # ── KPI Summary ────────────────────────────────────────────────────────────
    story += [
        _P("Resumen Financiero", "section"),
        _HR(),
        Spacer(1, 0.15 * cm),
        _kpi_summary_table(kpis),
        Spacer(1, 0.3 * cm),
        _P(
            "Nota: Todos los valores de ingresos se muestran sin IVA (neto). "
            "El EBITDA = Ingresos sin IVA − Gastos operacionales. "
            "Los gastos excluyen préstamos de socios y compras de activo fijo.",
            "info",
        ),
        Spacer(1, 0.4 * cm),
    ]

    # ── Break-even ─────────────────────────────────────────────────────────────
    story += [
        _P("Análisis de Break-even", "section"),
        _HR(),
        Spacer(1, 0.15 * cm),
        _breakeven_section(kpis, df),
        Spacer(1, 0.2 * cm),
        _P(
            "Break-even: unidades adicionales necesarias para que el EBITDA sea ≥ 0. "
            "EBITDA 25%: unidades adicionales para alcanzar un margen del 25%. "
            "Los ingresos 'c/IVA' representan el valor en caja (× 1.19).",
            "info",
        ),
        Spacer(1, 0.4 * cm),
    ]

    # ── Sales by product ───────────────────────────────────────────────────────
    story += [
        _P("Ventas por Producto (top 20)", "section"),
        _HR(),
        Spacer(1, 0.15 * cm),
        _sales_table(df),
        Spacer(1, 0.4 * cm),
    ]

    # ── Footer ─────────────────────────────────────────────────────────────────
    story += [
        _HR(BORDER),
        _P(f"FUDO Analytics · Oh My Pizza · {generated_at}", "footer"),
    ]

    doc.build(story)
    return buf.getvalue()
