"""Monthly KPI rows and the Uber Eats cash estimate.

The live dashboard still prices Uber at 25% of the menu line. These rows answer
a different question: how much money each month actually collected, and how much
of the Uber Eats portion is left after the service fee.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pandas as pd

from simulator.processing.constants import (
    DEFAULT_MONTH_SUELDOS,
    UBER_COLLECTED_COMMISSION_RATE,
)
from simulator.processing.engine import (
    get_unique_products,
    sales_clean_up_data,
    validate_expenses_columns,
    validate_sales_columns,
)

IVA = 1.19
_CHANNELS = ("caja", "walker", "pedidos_ya", "uber_eats", "otro")


class WorkbookError(ValueError):
    """A FUDO workbook failed validation. `payload` matches the upload API."""

    def __init__(self, message: str, payload: dict | None = None):
        super().__init__(message)
        self.payload = payload or {"error": message}


def _money(value: float) -> int:
    return int(round(float(value)))


def _ticket_key(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    as_int = numeric.round(0).astype("Int64").astype(str)
    text = series.astype(str).str.strip()
    return as_int.where(numeric.notna(), text)


def _channel(value: object) -> str:
    name = str(value).strip().lower().replace(" ", "")
    if name in {"uber_eats", "ubereats"}:
        return "uber_eats"
    if name in {"pedidos_ya", "pedidosya"}:
        return "pedidos_ya"
    if name == "walker":
        return "walker"
    if name in {"caja", "caja1", "local", "mostrador"}:
        return "caja"
    return "otro"


def read_discount_sheet(raw: bytes) -> pd.DataFrame | None:
    """Return the Descuentos sheet, or None when the workbook has no usable one."""
    try:
        book = pd.ExcelFile(io.BytesIO(raw))
    except Exception:
        return None
    if "Descuentos" not in book.sheet_names:
        return None
    try:
        frame = pd.read_excel(book, sheet_name="Descuentos")
    except Exception:
        return None
    if "Id. Venta" not in frame.columns or "Valor" not in frame.columns:
        return None
    return frame


def allocate_ticket_discounts(df: pd.DataFrame, discounts: pd.DataFrame | None) -> pd.DataFrame:
    """Spread each ticket discount across its lines in proportion to Precio.

    The line column `descuento` sums back to the ticket discount, including
    tickets whose lines are all priced at zero.
    """
    out = df.copy()
    out["descuento"] = 0.0
    if discounts is None or discounts.empty:
        return out
    kept = discounts
    if "Cancelado" in kept.columns:
        kept = kept[kept["Cancelado"] == "No"]
    if kept.empty:
        return out

    amounts = pd.to_numeric(kept["Valor"], errors="coerce").fillna(0.0)
    per_ticket = amounts.groupby(_ticket_key(kept["Id. Venta"])).sum()
    line_key = _ticket_key(out["Id. Venta"])
    price = pd.to_numeric(out["Precio"], errors="coerce").fillna(0.0)
    line_total = price.groupby(line_key).transform("sum")
    share = price.where(line_total > 0, 0.0) / line_total.where(line_total > 0, 1.0)
    mapped = line_key.map(per_ticket).fillna(0.0)
    out["descuento"] = (share * mapped).astype(float)
    remainder = mapped - out["descuento"].groupby(line_key).transform("sum")
    first = ~line_key.duplicated()
    out.loc[first, "descuento"] = out.loc[first, "descuento"] + remainder.loc[first]
    return out


def read_sales_workbook(raw: bytes) -> pd.DataFrame:
    """Clean an Adiciones sheet and attach discounts from the same file."""
    try:
        frame = pd.read_excel(io.BytesIO(raw), sheet_name="Adiciones")
    except Exception as exc:
        raise WorkbookError(f"No se pudo leer la hoja Adiciones: {exc}") from exc
    if "Cancelada" in frame.columns:
        frame = frame[frame["Cancelada"] == "No"].copy()
    valid, missing = validate_sales_columns(frame)
    if not valid:
        raise WorkbookError(
            "Invalid file format",
            {
                "error": "Invalid file format",
                "missing_columns": missing,
                "available_columns": frame.columns.tolist(),
            },
        )
    cleaned = sales_clean_up_data(frame)
    return allocate_ticket_discounts(cleaned, read_discount_sheet(raw))


def read_expenses_workbook(raw: bytes) -> pd.DataFrame:
    """Read a FUDO Gastos sheet (header sits on row 4)."""
    try:
        frame = pd.read_excel(io.BytesIO(raw), sheet_name="Gastos", skiprows=3)
    except Exception as exc:
        raise WorkbookError(f"No se pudo leer la hoja Gastos: {exc}") from exc
    valid, missing = validate_expenses_columns(frame)
    if not valid:
        raise WorkbookError(
            "Invalid file format",
            {
                "error": "Invalid file format",
                "missing_columns": missing,
                "available_columns": frame.columns.tolist(),
            },
        )
    frame = frame.copy()
    frame["Fecha"] = pd.to_datetime(frame["Fecha"], errors="coerce")
    return frame


def _ops_for_month(expenses: pd.DataFrame, month: str) -> dict[str, int | bool]:
    """Operational spend dated in `month`, split between people and Previred.

    Loans (Proveedor contains Prestamo) and capex (Activo Fijo) stay out,
    same rule as EBITDA. Cancelled rows stay out. Amounts are the FUDO
    importe, not divided by IVA. Previred is payroll for the file total, but
    it is reported apart so a typed salary does not replace it.
    """
    empty = {
        "gastos": 0,
        "pago_gente": 0,
        "previred": 0,
        "materia": 0,
        "tiene_remuneraciones": False,
    }
    if expenses is None or expenses.empty or "Fecha" not in expenses.columns:
        return empty
    frame = expenses.copy()
    frame["Fecha"] = pd.to_datetime(frame["Fecha"], errors="coerce")
    if "Cancelado" in frame.columns:
        frame = frame[frame["Cancelado"] == "No"]
    period = frame["Fecha"].dt.to_period("M").astype(str)
    frame = frame[period == month]
    if frame.empty:
        return empty
    provider = frame["Proveedor"].astype(str)
    is_loan = provider.str.contains("Prestamo", case=False, na=False)
    is_capex = frame["Categoría"] == "Activo Fijo"
    ops = frame[~is_loan & ~is_capex]
    if ops.empty:
        return empty
    category = ops["Categoría"].astype(str).str.strip().str.lower()
    subcategory = ops["Subcategoría"].astype(str).str.strip().str.lower()
    provider = ops["Proveedor"].astype(str)
    payroll = category.eq("personal") | subcategory.str.contains("remuner", na=False)
    is_previred = provider.str.contains("previred", case=False, na=False)
    people = payroll & ~is_previred
    previred_lines = payroll & is_previred
    ingredients = ops["Categoría"] == "Materia Prima"
    amounts = pd.to_numeric(ops["Importe"], errors="coerce").fillna(0)
    remuneraciones = people & subcategory.str.contains("remuner", na=False)
    return {
        "gastos": _money(amounts.sum()),
        "pago_gente": _money(amounts.loc[people].sum()),
        "previred": _money(amounts.loc[previred_lines].sum()),
        "materia": _money(amounts.loc[ingredients].sum()),
        "tiene_remuneraciones": bool(remuneraciones.any()),
    }


def _uber_cash(carta: float, cobrado: float) -> dict[str, int]:
    """Estimate the Uber deposit from FUDO, before ads and financing."""
    collected = _money(cobrado)
    commission = _money(collected * UBER_COLLECTED_COMMISSION_RATE)
    fee_with_tax = _money(commission * IVA)
    return {
        "carta": _money(carta),
        "descuentos": _money(carta - cobrado),
        "cobrado": collected,
        "comision_neta": commission,
        "tasa_servicio": fee_with_tax,
        "neto_estimado": collected - fee_with_tax,
    }


def monthly_performance(sales: pd.DataFrame, expenses: pd.DataFrame | None) -> list[dict[str, Any]]:
    """One KPI row per sales month, oldest first. Deltas are not filled in."""
    if sales is None or sales.empty:
        return []
    frame = sales.copy()
    if "created_at" not in frame.columns:
        frame["created_at"] = pd.to_datetime(frame.get("Creación"), errors="coerce")
    if "descuento" not in frame.columns:
        frame["descuento"] = 0.0
    frame["descuento"] = pd.to_numeric(frame["descuento"], errors="coerce").fillna(0.0)
    frame["Precio"] = pd.to_numeric(frame["Precio"], errors="coerce").fillna(0.0)
    frame["_cobrado"] = frame["Precio"] - frame["descuento"]
    frame["_month"] = frame["created_at"].dt.to_period("M").astype(str)
    frame["_channel"] = frame["Creada por"].map(_channel)

    rows: list[dict[str, Any]] = []
    for month, part in frame.groupby("_month", sort=True):
        if month in {"NaT", "nan"}:
            continue
        carta = float(part["Precio"].sum())
        cobrado = float(part["_cobrado"].sum())
        ops = _ops_for_month(expenses, str(month))
        gastos = int(ops["gastos"])
        pago_gente = int(ops["pago_gente"])
        previred = int(ops["previred"])
        materia = int(ops["materia"])
        cobrado_sin_iva = _money(cobrado / IVA)
        channels = {name: 0 for name in _CHANNELS}
        for channel, amount in part.groupby("_channel")["_cobrado"].sum().items():
            key = channel if channel in channels else "otro"
            channels[key] += _money(amount)
        uber = part[part["_channel"] == "uber_eats"]
        rows.append(
            {
                "month": str(month),
                "tickets": int(part["Id. Venta"].nunique()),
                "cobrado": _money(cobrado),
                "cobrado_sin_iva": cobrado_sin_iva,
                "descuentos": _money(carta - cobrado),
                "gastos_ops": gastos,
                "sueldos": pago_gente + previred,
                "pago_gente": pago_gente,
                "previred": previred,
                "tiene_remuneraciones": bool(ops["tiene_remuneraciones"]),
                "materia_prima": materia,
                "ebitda": cobrado_sin_iva - gastos,
                "channels": channels,
                "uber": _uber_cash(float(uber["Precio"].sum()), float(uber["_cobrado"].sum())),
            }
        )
    return rows


def people_pay_fallback(row: dict[str, Any]) -> int:
    """Where the month starts before anyone types a salary.

    A remuneraciones line starts from that payment to people. Previred is not
    part of it. A month without one — nothing, or only trial payments — starts
    from ``DEFAULT_MONTH_SUELDOS``, which is also only the payment to people.
    Older stored rows have no flag and keep the stand-in until the archive is
    loaded again.
    """
    if row.get("tiene_remuneraciones"):
        if row.get("pago_gente") is not None:
            return int(row["pago_gente"])
        return int(row.get("sueldos") or 0)
    return DEFAULT_MONTH_SUELDOS


def with_payroll_and_statement(
    row: dict[str, Any], sueldos_usados: int, statement: dict | None
) -> dict[str, Any]:
    """Rebuild the month result with a payment-to-people figure.

    That figure replaces ``pago_gente`` only. Previred stays inside the
    expenses. Rows saved before the split treat the whole ``sueldos`` number
    as the payment being replaced. The Uber cost in ``resultado`` is the PDF
    service fee net of IVA when the statement exists, otherwise the 26%
    estimate. The bank deposit is ``uber_pdf.neto``.
    """
    current = dict(row)
    if "pago_gente" in current and current.get("pago_gente") is not None:
        pago = int(current.get("pago_gente") or 0)
        previred = int(current.get("previred") or 0)
    else:
        pago = int(current.get("sueldos") or 0)
        previred = 0
    gastos_ops = int(current.get("gastos_ops") or 0)
    gastos_sin_sueldos = gastos_ops - pago
    usados = int(sueldos_usados)
    ebitda = int(current["cobrado_sin_iva"]) - gastos_sin_sueldos - usados
    uber = dict(current.get("uber") or {})
    estimate = int(uber.get("comision_neta") or 0)
    if statement and statement.get("tasa") is not None:
        comision = _money(abs(statement["tasa"]) / IVA)
        fuente = "pdf"
    else:
        comision = estimate
        fuente = "estimado"
    current.update(
        {
            "sueldos_fudo": pago,
            "previred": previred,
            "sueldos_usados": usados,
            "gastos_sin_sueldos": gastos_sin_sueldos,
            "ebitda": ebitda,
            "comision_uber": comision,
            "comision_fuente": fuente,
            "resultado": ebitda - comision,
            "uber_pdf": statement,
        }
    )
    return current


def apply_deltas(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Set each row's change against the previous month in the list."""
    ordered = sorted(rows, key=lambda row: row["month"])
    previous = None
    stamped: list[dict[str, Any]] = []
    for row in ordered:
        current = dict(row)
        if previous is None:
            current["delta_cobrado_pct"] = None
            current["delta_ebitda"] = None
            current["delta_resultado"] = None
        else:
            base = previous["cobrado_sin_iva"]
            current["delta_cobrado_pct"] = (
                round((current["cobrado_sin_iva"] - base) / abs(base) * 100, 1) if base else None
            )
            current["delta_ebitda"] = int(current["ebitda"] - previous["ebitda"])
            if previous.get("resultado") is not None and current.get("resultado") is not None:
                current["delta_resultado"] = int(current["resultado"] - previous["resultado"])
            else:
                current["delta_resultado"] = None
        stamped.append(current)
        previous = current
    return stamped


def sales_months_of(df: pd.DataFrame) -> list[str]:
    if df is None or df.empty or "created_at" not in df.columns:
        return []
    months = df["created_at"].dt.to_period("M").dropna().astype(str).unique().tolist()
    return sorted(months)


def load_fudo_archive(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read every ventas/gastos pair under a docs/2026-style directory."""
    sales_dir = root / "ventas"
    expense_dir = root / "gastos"
    sales_files = sorted(sales_dir.glob("*.xlsx")) if sales_dir.is_dir() else []
    expense_files = sorted(expense_dir.glob("*.xlsx")) if expense_dir.is_dir() else []
    if not sales_files or not expense_files:
        raise WorkbookError(f"No hay archivos de ventas y gastos en {root}")
    sales_parts = []
    for path in sales_files:
        try:
            sales_parts.append(read_sales_workbook(path.read_bytes()))
        except WorkbookError as exc:
            raise WorkbookError(f"{path.name}: {exc}") from exc
    expense_parts = []
    for path in expense_files:
        try:
            part = read_expenses_workbook(path.read_bytes())
        except WorkbookError as exc:
            raise WorkbookError(f"{path.name}: {exc}") from exc
        part["_source"] = path.name
        expense_parts.append(part)
    sales = pd.concat(sales_parts, ignore_index=True)
    expenses = drop_replaced_previred(pd.concat(expense_parts, ignore_index=True))
    return sales, expenses


def drop_replaced_previred(expenses: pd.DataFrame) -> pd.DataFrame:
    """Keep one Previred when a later gastos file corrects an earlier one.

    Same calendar date, provider Previred, two source files: the later file
    replaces the earlier. August 2026's $403.711 replaces July's $240.018,
    both dated 13 May. Two lines in the same file are both kept. The
    ``_source`` column is removed before the frame is stored.
    """
    if expenses is None or expenses.empty or "_source" not in expenses.columns:
        return expenses
    if "Proveedor" not in expenses.columns or "Fecha" not in expenses.columns:
        return expenses.drop(columns=["_source"])
    provider = expenses["Proveedor"].astype(str)
    is_previred = provider.str.contains("previred", case=False, na=False)
    dates = pd.to_datetime(expenses["Fecha"], errors="coerce").dt.normalize()
    drop_labels: list = []
    previred = expenses[is_previred]
    if not previred.empty:
        grouped = previred.groupby(dates.loc[previred.index], dropna=False).groups
        for day, labels in grouped.items():
            if pd.isna(day):
                continue
            sources = expenses.loc[labels, "_source"].astype(str)
            if sources.nunique() <= 1:
                continue
            latest = sources.max()
            drop_labels.extend(sources.index[sources != latest].tolist())
    kept = expenses.drop(index=drop_labels)
    return kept.drop(columns=["_source"]).reset_index(drop=True)


def archive_products(sales: pd.DataFrame) -> list[str]:
    return get_unique_products(sales)
