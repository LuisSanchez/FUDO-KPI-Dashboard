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
    n = int(n)
    sign = "−" if n < 0 else ""
    return sign + "$" + f"{abs(n):,}".replace(",", ".")


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

    total_ingreso = ing["total_ingreso_sin_iva"]
    comision_sin_iva = ing["comision_total"] / 1.19
    comision_pct_total = comision_sin_iva / total_ingreso * 100 if total_ingreso else 0
    margen_bruto_pct = (
        ing["total_margen_sin_iva"] / total_ingreso * 100 if total_ingreso else 0
    )

    rows = [
        ["Concepto", "Monto (s/IVA)", "Detalle"],
        [
            "Ingresos brutos sin IVA",
            _clp(total_ingreso),
            f"con IVA: {_clp(ing['total_ingreso'])}",
        ],
        [
            "  Comisión Uber Eats",
            _clp(-comision_sin_iva),
            f"{comision_pct_total:.1f}% de ingresos · 30% de pedidos Uber",
        ],
        [
            "  CMV (ingredientes s/IVA)",
            _clp(-ing["cmv"]),
            f"{ing['cmv_percentage']:.1f}% de ingresos",
        ],
        [
            "  Margen bruto (s/IVA)",
            _clp(ing["total_margen_sin_iva"]),
            f"{margen_bruto_pct:.1f}% · CMV + Comisión + Margen = 100%",
        ],
        ["Gastos operacionales", _clp(-gas["gastos_totales"]), ""],
        [
            "  Pagado",
            _clp(-gas["pagados_totales"]),
            f"Por pagar: {_clp(gas['por_pagar_totales'])}",
        ],
        [
            "EBITDA",
            _clp(ebitda_val),
            f"{ebitda_pct:.1f}% sobre ingresos",
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


def _sales_table(df_sales, categoria=None):
    rows_data = get_sales_table(df_sales)
    if not rows_data:
        return _P("Sin datos de ventas.", "bodysub")

    if categoria:
        rows_data = [r for r in rows_data if r.get("Categoría") == categoria]

    if not rows_data:
        return _P(f"Sin datos para la categoría '{categoria}'.", "bodysub")

    rows = [["Producto", "Cant.", "Ingreso s/IVA", "CMV%", "Comis.%", "Margen%"]]
    for r in rows_data[:20]:
        comis = r.get("comision_pct", 0) or 0
        rows.append(
            [
                r["Producto"][:34],
                str(int(r["cantidad"])),
                _clp(r["ingreso_sin_iva"]),
                f"{r['cmv_pct']:.1f}%",
                f"{comis:.1f}%" if comis > 0 else "—",
                f"{r['margen_pct']:.1f}%",
            ]
        )

    return _tbl(rows, [W * 0.38, W * 0.08, W * 0.20, W * 0.12, W * 0.10, W * 0.12])


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

    total_cmv = df_sales["costo_ingredientes_sin_iva"].sum()
    avg_ingreso_per_unit = total_ingreso / total_units
    # Contribution = ingreso − ingredient cost only.
    # Uber Eats commission is not in the expense file (Uber pays net),
    # so it does not scale with additional units in the EBITDA model.
    avg_contribution_per_unit = (total_ingreso - total_cmv) / total_units
    contribution_pct = (
        avg_contribution_per_unit / avg_ingreso_per_unit * 100
        if avg_ingreso_per_unit
        else 0
    )

    # Break-even: ebitda + x*c = 0  →  x = -ebitda / c
    if ebitda >= 0:
        be_units_needed = 0
        be_units_total = int(total_units)
        be_note = "Ya alcanzado"
    elif avg_contribution_per_unit > 0:
        be_units_needed = math.ceil(-ebitda / avg_contribution_per_unit)
        be_units_total = int(total_units) + be_units_needed
        be_note = ""
    else:
        return _P(
            "Contribución por unidad negativa. Revisar precios y costos.", "bodysub"
        )

    # 25% EBITDA: x = (0.25*I - ebitda) / (c - 0.25*i)
    denom_25 = avg_contribution_per_unit - 0.25 * avg_ingreso_per_unit
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
            f"EBITDA {ebt['ebitda_percentage']:.1f}% · ticket {_clp(avg_ingreso_per_unit)} · contrib. {contribution_pct:.1f}%",
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


# ── Expenses breakdown by category ────────────────────────────────────────────


def _expenses_breakdown(df_expenses, sales_months):
    df = df_expenses[df_expenses["Cancelado"] == "No"].copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df[df["Fecha"].dt.to_period("M").isin(sales_months)]

    is_loan = df["Proveedor"].str.contains("Prestamo", case=False, na=False)
    is_capex = df["Categoría"] == "Activo Fijo"
    df_ops = df[~is_loan & ~is_capex]

    if df_ops.empty:
        return _P("Sin gastos operacionales para el período.", "bodysub")

    by_cat = df_ops.groupby("Categoría")["Importe"].sum().sort_values(ascending=False)
    total = by_cat.sum()

    rows = [["Categoría", "Importe", "% del total", "Pagado", "Por pagar"]]
    for cat, amount in by_cat.items():
        paid = df_ops[
            (df_ops["Categoría"] == cat) & (df_ops["Estado del pago"] == "Pagado")
        ]["Importe"].sum()
        pending = df_ops[
            (df_ops["Categoría"] == cat) & (df_ops["Estado del pago"] == "A pagar")
        ]["Importe"].sum()
        pct = amount / total * 100 if total else 0
        rows.append(
            [
                cat,
                _clp(amount),
                f"{pct:.1f}%",
                _clp(paid) if paid else "—",
                _clp(pending) if pending else "—",
            ]
        )
    rows.append(["TOTAL", _clp(total), "100%", "", ""])

    extra = [
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), CARD_BG),
    ]
    return _tbl(rows, [W * 0.32, W * 0.18, W * 0.12, W * 0.19, W * 0.19], extra)


# ── Payables aging ─────────────────────────────────────────────────────────────


def _payables_aging(df_expenses, sales_months):
    df = df_expenses[df_expenses["Cancelado"] == "No"].copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df[df["Fecha"].dt.to_period("M").isin(sales_months)]

    is_loan = df["Proveedor"].str.contains("Prestamo", case=False, na=False)
    is_capex = df["Categoría"] == "Activo Fijo"
    df_ops = df[~is_loan & ~is_capex]
    df_pending = df_ops[df_ops["Estado del pago"] == "A pagar"].copy()

    if df_pending.empty:
        return _P("Sin deudas pendientes de pago.", "bodysub")

    df_pending["Fecha de vencimiento"] = pd.to_datetime(
        df_pending["Fecha de vencimiento"], errors="coerce"
    )
    today = datetime.date.today()

    def _bucket(row):
        due = row["Fecha de vencimiento"]
        if pd.isna(due):
            return "Sin fecha de vencimiento"
        days = (due.date() - today).days
        if days < 0:
            return "Vencido"
        if days <= 30:
            return "0–30 días"
        if days <= 60:
            return "31–60 días"
        if days <= 90:
            return "61–90 días"
        return "> 90 días"

    df_pending["bucket"] = df_pending.apply(_bucket, axis=1)

    bucket_order = [
        "Vencido",
        "0–30 días",
        "31–60 días",
        "61–90 días",
        "> 90 días",
        "Sin fecha de vencimiento",
    ]

    rows = [["Vencimiento", "Monto", "N°", "Proveedores principales"]]
    for bucket in bucket_order:
        subset = df_pending[df_pending["bucket"] == bucket]
        if subset.empty:
            continue
        amount = subset["Importe"].sum()
        top_provs = (
            subset.groupby("Proveedor")["Importe"].sum().nlargest(2).index.tolist()
        )
        prov_str = ", ".join(top_provs)[:40]
        rows.append([bucket, _clp(amount), str(len(subset)), prov_str])

    total_pending = df_pending["Importe"].sum()
    rows.append(["TOTAL POR PAGAR", _clp(total_pending), str(len(df_pending)), ""])

    extra = [
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), CARD_BG),
    ]
    # Highlight overdue row in red
    for i, row in enumerate(rows[1:], 1):
        if row[0] == "Vencido":
            extra.append(("TEXTCOLOR", (0, i), (1, i), RED))
            extra.append(("FONTNAME", (0, i), (1, i), "Helvetica-Bold"))

    return _tbl(rows, [W * 0.26, W * 0.20, W * 0.08, W * 0.46], extra)


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
    sales_months = df["created_at"].dt.to_period("M").unique()

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

    # ── Expenses breakdown ─────────────────────────────────────────────────────
    story += [
        _P("Composición de Gastos Operacionales", "section"),
        _HR(),
        Spacer(1, 0.15 * cm),
        _expenses_breakdown(df_expenses, sales_months),
        Spacer(1, 0.4 * cm),
    ]

    # ── Payables aging ─────────────────────────────────────────────────────────
    story += [
        _P("Aging de Cuentas por Pagar", "section"),
        _HR(),
        Spacer(1, 0.15 * cm),
        _payables_aging(df_expenses, sales_months),
        Spacer(1, 0.2 * cm),
        _P(
            "Referencia: vencimientos calculados al "
            + datetime.date.today().strftime("%d/%m/%Y")
            + ". Proveedores principales = los 2 de mayor monto por tramo.",
            "info",
        ),
        Spacer(1, 0.4 * cm),
    ]

    # ── Sales by product — Especialidades ─────────────────────────────────────
    story += [
        _P("Ventas por Producto — Especialidades (top 20)", "section"),
        _HR(),
        Spacer(1, 0.15 * cm),
        _sales_table(df, categoria="Especialidades"),
        Spacer(1, 0.4 * cm),
    ]

    # ── Sales by product — Extras ──────────────────────────────────────────────
    story += [
        _P("Ventas por Producto — Extras (top 20)", "section"),
        _HR(),
        Spacer(1, 0.15 * cm),
        _sales_table(df, categoria="Extras"),
        Spacer(1, 0.4 * cm),
    ]

    # ── Footer ─────────────────────────────────────────────────────────────────
    story += [
        _HR(BORDER),
        _P(f"FUDO Analytics · Oh My Pizza · {generated_at}", "footer"),
    ]

    doc.build(story)
    return buf.getvalue()
