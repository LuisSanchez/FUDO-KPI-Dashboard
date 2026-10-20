"""Local SQLite the chat is allowed to search."""

from types import SimpleNamespace

import pandas as pd
import pytest

from simulator.processing.monthly import _ops_for_month
from simulator.services.analytics_db import (
    QueryError,
    ensure_chat_database,
    run_select,
    write_database,
)


def _sales():
    return pd.DataFrame(
        {
            "Id. Venta": [10, 11],
            "created_at": pd.to_datetime(["2026-09-01", "2026-09-02"]),
            "Producto": ["Pepperoni", "Pepperoni"],
            "Categoría": ["Especialidades", "Especialidades"],
            "Cantidad": [1, 1],
            "Precio": [8990, 8990],
            "descuento": [0, 1000],
            "costo_ingredientes_sin_iva": [2000, 2000],
            "Creada por": ["caja1", "uber_eats"],
        }
    )


def _expenses():
    return pd.DataFrame(
        {
            "Fecha": ["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-05"],
            "Proveedor": ["ATILKO", "PREVIRED", "COZY BLF SPA", "Socio Prestamo Fernando", "Capex"],
            "Categoría": ["Servicios", "Personal", "Personal", "Servicios", "Activo Fijo"],
            "Subcategoría": [
                "Alquileres",
                "Remuneraciones y cotizaciones",
                "Remuneraciones y cotizaciones",
                "",
                "",
            ],
            "Importe": [1000, 400, 800, 5000, 9000],
            "Cancelado": ["No", "No", "No", "No", "No"],
        }
    )


def _build(tmp_path, statements=None, presented=None):
    dest = tmp_path / "chat.sqlite3"
    write_database(
        _sales(), _expenses(), statements or {}, presented or [], dest, "sesion", "firma"
    )
    return dest


def test_expense_flags_match_the_ebitda_filter(tmp_path):
    path = _build(tmp_path)
    counted = run_select(path, "SELECT SUM(importe) AS total FROM gastos WHERE entra_en_ebitda = 1")
    people = run_select(path, "SELECT SUM(importe) AS total FROM gastos WHERE es_pago_gente = 1")
    previred = run_select(path, "SELECT SUM(importe) AS total FROM gastos WHERE es_previred = 1")
    assert counted["filas"][0]["total"] == _ops_for_month(_expenses(), "2026-09")["gastos"]
    assert people["filas"][0]["total"] == 800
    assert previred["filas"][0]["total"] == 400
    channels = run_select(
        path, "SELECT canal, SUM(cobrado) AS total FROM ventas GROUP BY canal ORDER BY canal"
    )
    assert channels["filas"] == [
        {"canal": "caja", "total": 8990},
        {"canal": "uber_eats", "total": 7990},
    ]


def test_select_rejects_writes_and_a_second_statement(tmp_path):
    path = _build(tmp_path)
    for sql in (
        "DELETE FROM ventas",
        "SELECT 1; DROP TABLE ventas",
        "SELECT 1 -- oculto",
        "PRAGMA query_only = OFF",
        "",
    ):
        with pytest.raises(QueryError):
            run_select(path, sql)


def test_select_reports_truncation(tmp_path, monkeypatch):
    monkeypatch.setattr("simulator.services.analytics_db._MAX_ROWS", 1)
    path = _build(tmp_path)
    found = run_select(path, "SELECT ticket FROM ventas ORDER BY ticket")
    assert found["truncado"] is True
    assert len(found["filas"]) == 1


def test_empty_database_says_there_is_no_source(tmp_path):
    dest = tmp_path / "empty.sqlite3"
    write_database(None, None, {}, [], dest, "vacio", "nada")
    meta = run_select(dest, "SELECT valor FROM meta WHERE clave = 'fuente'")
    ventas = run_select(dest, "SELECT COUNT(*) AS n FROM ventas")
    assert meta["filas"][0]["valor"] == "vacio"
    assert ventas["filas"][0]["n"] == 0


@pytest.mark.django_db
def test_ensure_uses_a_saved_salary_and_then_the_cache(monkeypatch, tmp_path):
    from simulator.models import MonthAssumption

    sales, expenses = _sales(), _expenses()
    calls = {"frames": 0}

    def frames(_store):
        calls["frames"] += 1
        return sales, expenses, "sesion"

    monkeypatch.setattr("simulator.services.analytics_db._frames_for", frames)
    monkeypatch.setattr("simulator.services.analytics_db._signature", lambda _store: "firma")
    monkeypatch.setattr(
        "simulator.services.analytics_db.load_uber_statements",
        lambda _directory: {"2026-09": {"tasa": -1190, "neto": 5000, "pedidos": 2}},
    )
    MonthAssumption.objects.create(month="2026-09", sueldos=2_000_000)
    dest = tmp_path / "built.sqlite3"
    first = ensure_chat_database(SimpleNamespace(), dest)
    again = ensure_chat_database(SimpleNamespace(), dest)
    row = run_select(
        first,
        "SELECT sueldos_usados, sueldos_sugerido, comision_uber, deposito, comision_fuente "
        "FROM meses",
    )["filas"][0]
    assert again == first
    assert calls["frames"] == 1
    assert row["sueldos_usados"] == 2_000_000
    assert row["sueldos_sugerido"] == 800
    assert row["comision_uber"] == 1000
    assert row["deposito"] == 5000
    assert row["comision_fuente"] == "pdf"
