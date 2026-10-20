"""SQLite the chat can search. Rebuilt from the session, or from docs/2026.

The file is a cache. Month totals match the history screen: the typed payroll
replaces only the payment to people, Previred stays in expenses, and the Uber
cost is the PDF fee net of IVA. Line tables are there for the questions a
month total cannot answer.
"""

from __future__ import annotations

import re
import sqlite3
import threading
from pathlib import Path

import pandas as pd
from django.conf import settings

from simulator.models import MonthAssumption
from simulator.processing.monthly import (
    _channel,
    load_fudo_archive,
    monthly_performance,
    people_pay_fallback,
    with_payroll_and_statement,
)
from simulator.processing.uber_statements import load_uber_statements
from simulator.services.month_history import archive_root, statement_dir
from simulator.services.session_store import load_df

_LOCK = threading.Lock()
_MAX_ROWS = 200
_MAX_SQL = 4000
_FORBIDDEN = re.compile(
    r"\b(attach|detach|pragma|insert|update|delete|drop|alter|create|replace|vacuum|"
    r"load_extension|reindex|analyze)\b",
    re.IGNORECASE,
)

_REGLAS = (
    (
        "ebitda",
        "EBITDA = cobrado_sin_iva - gastos_sin_pago_gente - sueldos_usados. "
        "No restar otra vez la materia prima ni el costo de la línea de venta.",
    ),
    (
        "sueldos",
        "sueldos_usados reemplaza pago_gente y no se suma. No incluye Previred. "
        "Si tiene_remuneraciones es 0, el punto de partida es 1300000. "
        "Si sueldos_usados es distinto de sueldos_sugerido, alguien lo ajustó a mano.",
    ),
    (
        "previred",
        "El Previred queda dentro de los gastos del EBITDA. No está dentro de sueldos_usados.",
    ),
    (
        "uber",
        "resultado = ebitda - comision_uber. comision_uber es la tasa del PDF sin IVA "
        "(abs(tasa)/1.19) cuando hay liquidación; si no, el 26% de lo que pagó el cliente. "
        "deposito es lo que llegó al banco y no se resta. Anuncios y ajustes no entran en resultado.",
    ),
    (
        "iva",
        "Precio, descuento, cobrado de ventas e importe de gastos están como los registró FUDO. "
        "cobrado_sin_iva ya está dividido por 1.19. No dividir los gastos por 1.19.",
    ),
    (
        "fuera",
        "Préstamos (es_prestamo=1), activo fijo (es_activo_fijo=1) y filas canceladas "
        "(cancelado=1) no entran al EBITDA. entra_en_ebitda=0 las marca.",
    ),
    (
        "canales",
        "canal usa caja, walker, pedidos_ya, uber_eats u otro. caja incluye mostrador.",
    ),
)


class QueryError(ValueError):
    """The chat tried to run something other than a single read-only SELECT."""


def database_path(store) -> Path:
    key = re.sub(r"[^A-Za-z0-9_-]", "", str(getattr(store, "session_key", "") or "anon"))
    return Path(settings.BASE_DIR) / "var" / "chat" / f"{key[:40] or 'anon'}.sqlite3"


def ensure_chat_database(store, dest: Path | None = None) -> Path:
    """Return the session cache, rebuilding it when the source data changed."""
    dest = dest or database_path(store)
    signature = _signature(store)
    with _LOCK:
        if _stored_signature(dest) == signature:
            return dest
        sales, expenses, source = _frames_for(store)
        statements = load_uber_statements(statement_dir())
        raw = monthly_performance(sales, expenses) if sales is not None and not sales.empty else []
        assumptions = dict(MonthAssumption.objects.values_list("month", "sueldos"))
        presented = []
        for row in raw:
            fallback = people_pay_fallback(row)
            shown = with_payroll_and_statement(
                row, int(assumptions.get(row["month"], fallback)), statements.get(row["month"])
            )
            shown["sueldos_sugerido"] = fallback
            presented.append(shown)
        write_database(sales, expenses, statements, presented, dest, source, signature)
        return dest


def write_database(
    sales: pd.DataFrame | None,
    expenses: pd.DataFrame | None,
    statements: dict,
    presented: list[dict],
    dest: Path,
    source: str,
    signature: str,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporary = dest.with_suffix(".building")
    if temporary.exists():
        temporary.unlink()
    connection = sqlite3.connect(temporary)
    try:
        connection.executescript(_SCHEMA)
        connection.executemany(
            "INSERT INTO ventas VALUES (?,?,?,?,?,?,?,?,?,?,?)", _sales_rows(sales)
        )
        connection.executemany(
            "INSERT INTO gastos VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", _expense_rows(expenses)
        )
        connection.executemany(
            "INSERT INTO uber VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", _uber_rows(statements)
        )
        connection.executemany(
            "INSERT INTO meses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            _month_rows(presented),
        )
        connection.executemany("INSERT INTO reglas VALUES (?,?)", _REGLAS)
        connection.executemany(
            "INSERT INTO meta VALUES (?,?)",
            (("fuente", source), ("firma", signature)),
        )
        connection.commit()
    finally:
        connection.close()
    temporary.replace(dest)


def run_select(path: Path, sql: str) -> dict:
    """Run one read-only SELECT. Raises QueryError when the statement is not."""
    statement = _validated_sql(sql)
    uri = f"file:{path}?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=5)
    try:
        connection.execute("PRAGMA query_only = ON")
        cursor = connection.execute(statement)
        fetched = cursor.fetchmany(_MAX_ROWS + 1)
        truncated = len(fetched) > _MAX_ROWS
        columns = [item[0] for item in cursor.description or []]
        rows = [dict(zip(columns, row, strict=True)) for row in fetched[:_MAX_ROWS]]
    except sqlite3.Error as exc:
        raise QueryError(f"La consulta no se pudo ejecutar: {exc}") from exc
    finally:
        connection.close()
    return {"columnas": columns, "filas": rows, "truncado": truncated}


def _validated_sql(sql: str) -> str:
    statement = (sql or "").strip()
    if statement.endswith(";"):
        statement = statement[:-1].strip()
    if not statement:
        raise QueryError("Falta el SELECT.")
    if len(statement) > _MAX_SQL:
        raise QueryError("La consulta es demasiado larga.")
    if ";" in statement or "--" in statement or "/*" in statement:
        raise QueryError("Solo un SELECT, sin comentarios ni otra sentencia.")
    if not re.match(r"(?is)^(select|with)\b", statement):
        raise QueryError("Solo se acepta un SELECT de lectura.")
    if _FORBIDDEN.search(statement):
        raise QueryError("Esa consulta no está permitida. Usa solo SELECT.")
    return statement


def _stored_signature(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        found = run_select(path, "SELECT valor FROM meta WHERE clave = 'firma'")
    except (QueryError, sqlite3.Error, OSError):
        return None
    rows = found["filas"]
    if not rows:
        return None
    return str(rows[0].get("valor") or "")


def _signature(store) -> str:
    assumptions = MonthAssumption.objects.order_by("month").values_list(
        "month", "sueldos", "updated_at"
    )
    assumption_part = "|".join(
        f"{month}:{sueldos}:{stamp}" for month, sueldos, stamp in assumptions
    )
    pdf_part = _tree_stamp(statement_dir())
    sales_pickle = getattr(store, "sales_df_pickle", None)
    expenses_pickle = getattr(store, "expenses_df_pickle", None)
    if sales_pickle is not None and expenses_pickle is not None:
        updated = getattr(store, "updated_at", None)
        return f"sesion|{updated}|{assumption_part}|{pdf_part}"
    if archive_root() is not None:
        return f"archivo|{_tree_stamp(archive_root())}|{assumption_part}|{pdf_part}"
    return f"vacio|{assumption_part}|{pdf_part}"


def _tree_stamp(root: Path | None) -> str:
    if root is None or not root.exists():
        return ""
    stamps = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".xlsx", ".pdf"}:
            stamps.append(f"{path.name}:{path.stat().st_mtime_ns}")
    return ",".join(stamps)


def _frames_for(store) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    sales_pickle = getattr(store, "sales_df_pickle", None)
    expenses_pickle = getattr(store, "expenses_df_pickle", None)
    if sales_pickle is not None and expenses_pickle is not None:
        return load_df(sales_pickle), load_df(expenses_pickle), "sesion"
    root = archive_root()
    if root is not None:
        sales, expenses = load_fudo_archive(root)
        return sales, expenses, "archivo"
    sales = load_df(sales_pickle) if sales_pickle is not None else pd.DataFrame()
    expenses = load_df(expenses_pickle) if expenses_pickle is not None else pd.DataFrame()
    if sales_pickle is not None or expenses_pickle is not None:
        return sales, expenses, "sesion"
    return sales, expenses, "vacio"


def _sales_rows(frame: pd.DataFrame | None) -> list[tuple]:
    if frame is None or frame.empty:
        return []
    rows = []
    created = (
        pd.to_datetime(frame["created_at"], errors="coerce")
        if "created_at" in frame.columns
        else pd.Series(pd.NaT, index=frame.index)
    )
    for index, row in frame.iterrows():
        when = created.loc[index]
        if isinstance(when, pd.Series):
            when = when.iloc[0]
        month = "" if pd.isna(when) else str(when.to_period("M"))
        day = "" if pd.isna(when) else when.strftime("%Y-%m-%d")
        precio = _money(row.get("Precio"))
        descuento = _money(row.get("descuento"))
        rows.append(
            (
                month,
                day,
                _ticket(row.get("Id. Venta")),
                _text(row.get("Producto")),
                _text(row.get("Categoría")),
                _quantity(row.get("Cantidad")),
                precio,
                descuento,
                precio - descuento,
                _money(row.get("costo_ingredientes_sin_iva")),
                _channel(row.get("Creada por")),
            )
        )
    return rows


def _expense_rows(frame: pd.DataFrame | None) -> list[tuple]:
    if frame is None or frame.empty or "Fecha" not in frame.columns:
        return []
    rows = []
    dated = pd.to_datetime(frame["Fecha"], errors="coerce")
    for index, row in frame.iterrows():
        when = dated.loc[index]
        if isinstance(when, pd.Series):
            when = when.iloc[0]
        month = "" if pd.isna(when) else str(when.to_period("M"))
        day = "" if pd.isna(when) else when.strftime("%Y-%m-%d")
        provider = _text(row.get("Proveedor"))
        category = _text(row.get("Categoría"))
        subcategory = _text(row.get("Subcategoría"))
        cancelled = _text(row.get("Cancelado")).lower() == "si"
        loan = "prestamo" in provider.lower()
        capex = category == "Activo Fijo"
        previred = "previred" in provider.lower()
        payroll = category.lower() == "personal" or "remuner" in subcategory.lower()
        counts = not cancelled and not loan and not capex
        rows.append(
            (
                month,
                day,
                provider,
                category,
                subcategory,
                _money(row.get("Importe")),
                int(cancelled),
                int(loan),
                int(capex),
                int(previred and counts),
                int(payroll and counts and not previred),
                int(counts),
            )
        )
    return rows


def _uber_rows(statements: dict | None) -> list[tuple]:
    rows = []
    for month in sorted(statements or {}):
        item = statements[month] or {}
        tasa = item.get("tasa")
        comision = None if tasa is None else int(round(abs(int(tasa)) / 1.19))
        rows.append(
            (
                month,
                item.get("pedidos"),
                item.get("ventas"),
                item.get("ofertas"),
                tasa,
                item.get("tasa_total"),
                item.get("cargo_oferta"),
                item.get("anuncios"),
                item.get("ajuste_marketing"),
                item.get("ajustes"),
                item.get("neto"),
                comision,
            )
        )
    return rows


def _month_rows(presented: list[dict]) -> list[tuple]:
    rows = []
    for row in presented:
        channels = row.get("channels") or {}
        uber = row.get("uber") or {}
        pdf = row.get("uber_pdf") or {}
        rows.append(
            (
                row.get("month"),
                _nullable_int(row.get("tickets")),
                _nullable_int(row.get("cobrado")),
                _nullable_int(row.get("cobrado_sin_iva")),
                _nullable_int(row.get("gastos_ops")),
                _nullable_int(row.get("gastos_sin_sueldos")),
                _nullable_int(
                    row.get("pago_gente") if "pago_gente" in row else row.get("sueldos_fudo")
                ),
                _nullable_int(row.get("previred")),
                int(bool(row.get("tiene_remuneraciones"))),
                _nullable_int(row.get("sueldos_usados")),
                _nullable_int(row.get("sueldos_sugerido")),
                _nullable_int(row.get("ebitda")),
                _nullable_int(row.get("comision_uber")),
                row.get("comision_fuente") or "",
                _nullable_int(row.get("resultado")),
                _nullable_int(uber.get("cobrado")),
                _nullable_int(uber.get("neto_estimado")),
                _nullable_int(pdf.get("neto")) if pdf else None,
                _nullable_int(channels.get("caja")),
                _nullable_int(channels.get("walker")),
                _nullable_int(channels.get("pedidos_ya")),
                _nullable_int(channels.get("otro")),
            )
        )
    return rows


def _text(value) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value).strip()


def _ticket(value) -> str:
    text = _text(value)
    if not text:
        return ""
    try:
        number = float(text)
    except ValueError:
        return text
    if number.is_integer():
        return str(int(number))
    return text


def _money(value) -> int:
    if value is None:
        return 0
    try:
        if pd.isna(value):
            return 0
    except TypeError:
        pass
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return 0


def _nullable_int(value) -> int | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _quantity(value) -> float:
    if value is None:
        return 0.0
    try:
        if pd.isna(value):
            return 0.0
    except TypeError:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


_SCHEMA = """
CREATE TABLE ventas (
    mes TEXT,
    fecha TEXT,
    ticket TEXT,
    producto TEXT,
    categoria TEXT,
    cantidad REAL,
    precio INTEGER,
    descuento INTEGER,
    cobrado INTEGER,
    costo_sin_iva INTEGER,
    canal TEXT
);
CREATE TABLE gastos (
    mes TEXT,
    fecha TEXT,
    proveedor TEXT,
    categoria TEXT,
    subcategoria TEXT,
    importe INTEGER,
    cancelado INTEGER,
    es_prestamo INTEGER,
    es_activo_fijo INTEGER,
    es_previred INTEGER,
    es_pago_gente INTEGER,
    entra_en_ebitda INTEGER
);
CREATE TABLE uber (
    mes TEXT,
    pedidos INTEGER,
    ventas INTEGER,
    ofertas INTEGER,
    tasa INTEGER,
    tasa_total INTEGER,
    cargo_oferta INTEGER,
    anuncios INTEGER,
    ajuste_marketing INTEGER,
    ajustes INTEGER,
    deposito INTEGER,
    comision_neta INTEGER
);
CREATE TABLE meses (
    mes TEXT,
    tickets INTEGER,
    cobrado INTEGER,
    cobrado_sin_iva INTEGER,
    gastos_ops INTEGER,
    gastos_sin_pago_gente INTEGER,
    pago_gente INTEGER,
    previred INTEGER,
    tiene_remuneraciones INTEGER,
    sueldos_usados INTEGER,
    sueldos_sugerido INTEGER,
    ebitda INTEGER,
    comision_uber INTEGER,
    comision_fuente TEXT,
    resultado INTEGER,
    uber_cobrado INTEGER,
    uber_neto_estimado INTEGER,
    deposito INTEGER,
    caja INTEGER,
    walker INTEGER,
    pedidos_ya INTEGER,
    otro INTEGER
);
CREATE TABLE reglas (tema TEXT, texto TEXT);
CREATE TABLE meta (clave TEXT, valor TEXT);
CREATE INDEX idx_ventas_mes ON ventas(mes);
CREATE INDEX idx_ventas_producto ON ventas(producto);
CREATE INDEX idx_gastos_mes ON gastos(mes);
CREATE INDEX idx_gastos_proveedor ON gastos(proveedor);
"""
