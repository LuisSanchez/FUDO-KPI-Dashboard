"""Persist one KPI row per month on the session, independent of the working upload.

Stored rows stay as `monthly_performance` left them: EBITDA still includes the
file payroll and does not subtract Uber. Payroll overrides and the PDF
settlement are applied only in `present_history`, on the way out.
"""

from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings

from simulator.models import MonthAssumption
from simulator.processing.constants import DEFAULT_MONTH_SUELDOS, UBER_COLLECTED_COMMISSION_RATE
from simulator.processing.monthly import (
    apply_deltas,
    monthly_performance,
    people_pay_fallback,
    sales_months_of,
    with_payroll_and_statement,
)
from simulator.processing.uber_statements import load_uber_statements
from simulator.services.session_store import load_df

_MAX_SUELDOS = 100_000_000
_MONTH_ERROR = "El mes tiene que ser YYYY-MM."
_SUELDOS_ERROR = "El sueldo tiene que ser un entero entre 0 y 100.000.000."


class SueldosError(ValueError):
    """The payroll override could not be saved."""


def archive_root() -> Path | None:
    """Local docs/2026 folder, when this checkout has the FUDO workbooks."""
    root = Path(settings.BASE_DIR).parent / "docs" / "2026"
    if (root / "ventas").is_dir() and (root / "gastos").is_dir():
        return root
    return None


def history_rows(store) -> list[dict]:
    raw = list((store.month_history or {}).values())
    return apply_deltas(raw)


def replace_history(store, rows: list[dict]) -> list[dict]:
    stamped = apply_deltas(rows)
    store.month_history = {row["month"]: row for row in stamped}
    return stamped


def merge_history(store, rows: list[dict]) -> list[dict]:
    """Insert or replace the given months and keep every other saved month."""
    history = {row["month"]: row for row in history_rows(store)}
    for row in rows:
        history[row["month"]] = row
    return replace_history(store, list(history.values()))


def drop_months(store, months: list[str]) -> list[dict]:
    history = {row["month"]: row for row in history_rows(store)}
    for month in months:
        history.pop(month, None)
    return replace_history(store, list(history.values()))


def statement_dir() -> Path | None:
    root = archive_root()
    if root is None:
        return None
    folder = root / "uber-eats"
    return folder if folder.is_dir() else None


def present_history(store) -> list[dict]:
    """Rows for the API. Never write this result back into `month_history`."""
    assumptions = dict(MonthAssumption.objects.values_list("month", "sueldos"))
    statements = load_uber_statements(statement_dir())
    presented = []
    for row in (store.month_history or {}).values():
        month = str(row.get("month") or "")
        fallback = people_pay_fallback(row)
        usados = int(assumptions.get(month, fallback))
        shown = with_payroll_and_statement(row, usados, statements.get(month))
        shown["sueldos_sugerido"] = fallback
        presented.append(shown)
    return apply_deltas(presented)


def history_payload(store) -> dict:
    return {
        "months": present_history(store),
        "archive_available": archive_root() is not None,
        "commission_rate": UBER_COLLECTED_COMMISSION_RATE,
        "default_sueldos": DEFAULT_MONTH_SUELDOS,
    }


def _check_month(month: str) -> str:
    match = re.fullmatch(r"(\d{4})-(\d{2})", month or "")
    if not match or not 1 <= int(match.group(2)) <= 12:
        raise SueldosError(_MONTH_ERROR)
    return month


def _coerce_sueldos(value) -> int:
    if isinstance(value, bool) or isinstance(value, float) or value is None:
        raise SueldosError(_SUELDOS_ERROR)
    if isinstance(value, str):
        text = value.strip()
        if not text.isdigit():
            raise SueldosError(_SUELDOS_ERROR)
        value = int(text)
    if not isinstance(value, int) or value < 0 or value > _MAX_SUELDOS:
        raise SueldosError(_SUELDOS_ERROR)
    return value


def save_month_sueldos(month: str, raw) -> int:
    """Replace the payroll used to evaluate `month`. Zero is a real value."""
    checked = _check_month(month)
    sueldos = _coerce_sueldos(raw)
    MonthAssumption.objects.update_or_create(month=checked, defaults={"sueldos": sueldos})
    return sueldos


def clear_month_sueldos(month: str) -> None:
    """Drop the override so the month falls back to `DEFAULT_MONTH_SUELDOS`."""
    checked = _check_month(month)
    MonthAssumption.objects.filter(month=checked).delete()


def snapshot_uploaded(store, months: list[str] | None = None) -> list[dict]:
    """Rebuild rows from the working DataFrames and merge those months in."""
    if store.sales_df_pickle is None or store.expenses_df_pickle is None:
        return history_rows(store)
    sales = load_df(store.sales_df_pickle)
    expenses = load_df(store.expenses_df_pickle)
    # A partial expense file must not overwrite a month that was saved from the
    # full archive. Only refresh history when this upload covers every sales month
    # currently in the session.
    if months is not None and not set(sales_months_of(sales)).issubset(set(months)):
        return history_rows(store)
    rows = monthly_performance(sales, expenses)
    if months is not None:
        keep = set(months)
        rows = [row for row in rows if row["month"] in keep]
    return merge_history(store, rows)
