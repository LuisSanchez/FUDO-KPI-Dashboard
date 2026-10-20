"""Monthly KPI rows and the Uber cash estimate."""

from pathlib import Path

import pandas as pd
import pytest

from simulator.processing.monthly import (
    allocate_ticket_discounts,
    apply_deltas,
    monthly_performance,
    read_sales_workbook,
)

ROOT = Path(__file__).resolve().parents[3]
SEP_SALES = ROOT / "docs" / "2026" / "ventas" / "2026-09-ventas.xlsx"
SEP_EXPENSES = ROOT / "docs" / "2026" / "gastos" / "2026-09-gastos.xlsx"


def _sales(rows):
    frame = pd.DataFrame(rows)
    frame["created_at"] = pd.to_datetime(frame["Creación"])
    return frame


def test_discount_is_spread_by_line_price_and_sums_back():
    sales = pd.DataFrame(
        {
            "Id. Venta": [1, 1, 2],
            "Precio": [8000, 2000, 5000],
        }
    )
    discounts = pd.DataFrame(
        {
            "Id. Venta": [1, 2, 2],
            "Valor": [1000, 500, 100],
            "Cancelado": ["No", "No", "Si"],
        }
    )
    out = allocate_ticket_discounts(sales, discounts)
    assert list(out["descuento"].round(2)) == [800.0, 200.0, 500.0]


def test_zero_price_ticket_keeps_the_discount_on_the_first_line():
    sales = pd.DataFrame({"Id. Venta": [7, 7], "Precio": [0, 0]})
    discounts = pd.DataFrame({"Id. Venta": [7], "Valor": [1500], "Cancelado": ["No"]})
    out = allocate_ticket_discounts(sales, discounts)
    assert out["descuento"].sum() == 1500
    assert out["descuento"].iloc[0] == 1500


def test_uber_neto_is_26_percent_of_what_the_customer_paid():
    sales = _sales(
        {
            "Id. Venta": [1, 2],
            "Creación": ["2026-09-01", "2026-09-02"],
            "Precio": [15980, 8990],
            "descuento": [7990, 0],
            "Creada por": ["uber_eats", "caja1"],
            "Cantidad": [1, 1],
        }
    )
    expenses = pd.DataFrame(
        {
            "Fecha": ["2026-09-01", "2026-09-03", "2026-09-04", "2026-09-05"],
            "Proveedor": ["ATILKO", "Socio Prestamo Fernando", "Capex", "X"],
            "Categoría": ["Servicios", "Servicios", "Activo Fijo", "Personal"],
            "Subcategoría": ["Alquileres", "", "", "Remuneraciones y cotizaciones"],
            "Importe": [1000, 5000, 9000, 300],
            "Cancelado": ["No", "No", "No", "Si"],
        }
    )
    rows = monthly_performance(sales, expenses)
    assert len(rows) == 1
    uber = rows[0]["uber"]
    # Customer paid 15980 − 7990. Fee is 26% of that, then IVA on the fee.
    assert uber["cobrado"] == 7990
    assert uber["comision_neta"] == round(7990 * 0.26)
    assert uber["tasa_servicio"] == round(uber["comision_neta"] * 1.19)
    assert uber["neto_estimado"] == uber["cobrado"] - uber["tasa_servicio"]
    assert rows[0]["channels"]["uber_eats"] == 7990
    assert rows[0]["channels"]["caja"] == 8990
    # Loan, capex and the cancelled payroll line stay out of the month.
    assert rows[0]["gastos_ops"] == 1000
    assert rows[0]["sueldos"] == 0
    assert rows[0]["ebitda"] == round((7990 + 8990) / 1.19) - 1000


def test_deltas_compare_each_month_with_the_one_before():
    rows = apply_deltas(
        [
            {"month": "2026-02", "cobrado_sin_iva": 80, "ebitda": -20},
            {"month": "2026-01", "cobrado_sin_iva": 100, "ebitda": -50},
        ]
    )
    assert [row["month"] for row in rows] == ["2026-01", "2026-02"]
    assert rows[0]["delta_cobrado_pct"] is None
    assert rows[0]["delta_resultado"] is None
    assert rows[1]["delta_cobrado_pct"] == -20.0
    assert rows[1]["delta_ebitda"] == 30
    assert rows[1]["delta_resultado"] is None


def test_previred_stays_in_expenses_and_remuneraciones_start_from_the_file():
    from simulator.processing.monthly import people_pay_fallback, with_payroll_and_statement

    sales = _sales(
        {
            "Id. Venta": [1],
            "Creación": ["2026-02-05"],
            "Precio": [11900],
            "descuento": [0],
            "Creada por": ["caja1"],
            "Cantidad": [1],
        }
    )
    expenses = pd.DataFrame(
        {
            "Fecha": ["2026-02-05", "2026-02-26", "2026-02-10"],
            "Proveedor": ["COZY BLF SPA", "PREVIRED", "JULIEHT"],
            "Categoría": ["Personal", "Personal", "Personal"],
            "Subcategoría": [
                "Remuneraciones y cotizaciones",
                "Remuneraciones y cotizaciones",
                "Personal de prueba y Otros",
            ],
            "Importe": [1000, 400, 50],
            "Cancelado": ["No", "No", "No"],
        }
    )
    row = monthly_performance(sales, expenses)[0]
    assert row["pago_gente"] == 1050
    assert row["previred"] == 400
    assert row["sueldos"] == 1450
    assert row["tiene_remuneraciones"] is True
    assert people_pay_fallback(row) == 1050
    shown = with_payroll_and_statement(row, 1050, None)
    assert shown["previred"] == 400
    assert shown["gastos_sin_sueldos"] == row["gastos_ops"] - 1050
    assert shown["ebitda"] == row["cobrado_sin_iva"] - row["gastos_ops"]


def test_trial_payments_use_the_people_stand_in_and_keep_previred():
    from simulator.processing.constants import DEFAULT_MONTH_SUELDOS
    from simulator.processing.monthly import people_pay_fallback, with_payroll_and_statement

    sales = _sales(
        {
            "Id. Venta": [1],
            "Creación": ["2026-06-11"],
            "Precio": [11900],
            "descuento": [0],
            "Creada por": ["caja1"],
            "Cantidad": [1],
        }
    )
    expenses = pd.DataFrame(
        {
            "Fecha": ["2026-06-11", "2026-06-15"],
            "Proveedor": ["JULIEHT", "PREVIRED"],
            "Categoría": ["Personal", "Personal"],
            "Subcategoría": ["Personal de prueba y Otros", "Remuneraciones y cotizaciones"],
            "Importe": [50, 400],
            "Cancelado": ["No", "No"],
        }
    )
    row = monthly_performance(sales, expenses)[0]
    assert row["pago_gente"] == 50
    assert row["previred"] == 400
    assert row["tiene_remuneraciones"] is False
    assert people_pay_fallback(row) == DEFAULT_MONTH_SUELDOS
    shown = with_payroll_and_statement(row, DEFAULT_MONTH_SUELDOS, None)
    assert shown["gastos_sin_sueldos"] == row["gastos_ops"] - 50
    assert shown["ebitda"] == (
        row["cobrado_sin_iva"] - shown["gastos_sin_sueldos"] - DEFAULT_MONTH_SUELDOS
    )


def test_later_gastos_file_replaces_previred_on_the_same_date():
    from simulator.processing.monthly import drop_replaced_previred

    frame = pd.DataFrame(
        {
            "Fecha": ["2026-05-13", "2026-05-13", "2026-05-13", "2026-04-13"],
            "Proveedor": ["PREVIRED", "PREVIRED", "ATILKO", "PREVIRED"],
            "Importe": [240_018, 403_711, 10, 442_583],
            "_source": [
                "2026-07-gastos.xlsx",
                "2026-08-gastos.xlsx",
                "2026-07-gastos.xlsx",
                "2026-05-gastos.xlsx",
            ],
        }
    )
    out = drop_replaced_previred(frame)
    assert "_source" not in out.columns
    assert sorted(out["Importe"].tolist()) == [10, 403_711, 442_583]


def test_two_previred_lines_in_the_same_file_are_kept():
    from simulator.processing.monthly import drop_replaced_previred

    frame = pd.DataFrame(
        {
            "Fecha": ["2026-05-13", "2026-05-13"],
            "Proveedor": ["PREVIRED", "PREVIRED"],
            "Importe": [100, 200],
            "_source": ["2026-05-gastos.xlsx", "2026-05-gastos.xlsx"],
        }
    )
    out = drop_replaced_previred(frame)
    assert int(out["Importe"].sum()) == 300


def test_payroll_input_replaces_the_file_amount():
    from simulator.processing.monthly import with_payroll_and_statement

    row = {
        "month": "2026-09",
        "cobrado_sin_iva": 5_000,
        "gastos_ops": 1_300,
        "sueldos": 300,
        "ebitda": 3_700,
        "uber": {"comision_neta": 100},
    }
    out = with_payroll_and_statement(row, 1_000, None)
    assert "sueldos_usados" not in row
    assert out["sueldos_fudo"] == 300
    assert out["gastos_sin_sueldos"] == 1_000
    assert out["sueldos_usados"] == 1_000
    # 1_000 replaces the 300 already inside gastos_ops. It is not added on top.
    assert out["ebitda"] == 5_000 - 1_000 - 1_000
    assert out["comision_fuente"] == "estimado"
    assert out["comision_uber"] == 100
    assert out["resultado"] == out["ebitda"] - 100
    assert out["uber_pdf"] is None


def test_pdf_fee_counts_net_of_iva_not_the_cash_withholding():
    from simulator.processing.monthly import with_payroll_and_statement

    row = {
        "month": "2026-09",
        "cobrado_sin_iva": 6_000,
        "gastos_ops": 8_000,
        "sueldos": 0,
        "uber": {"comision_neta": 722_790},
    }
    statement = {"tasa": -864_581, "neto": 655_892, "anuncios": -330_468, "ajustes": -918_264}
    out = with_payroll_and_statement(row, 1_300_000, statement)
    assert out["gastos_sin_sueldos"] == 8_000
    assert out["ebitda"] == 6_000 - 8_000 - 1_300_000
    assert out["comision_fuente"] == "pdf"
    # 864_581 / 1.19, not the cash tasa and not the 26% estimate.
    assert out["comision_uber"] == 726_539
    assert out["resultado"] == out["ebitda"] - 726_539
    assert out["uber_pdf"]["neto"] == 655_892


def test_resultado_delta_needs_both_months():
    rows = apply_deltas(
        [
            {"month": "2026-01", "cobrado_sin_iva": 100, "ebitda": -50, "resultado": -80},
            {"month": "2026-02", "cobrado_sin_iva": 80, "ebitda": -20, "resultado": -30},
            {"month": "2026-03", "cobrado_sin_iva": 90, "ebitda": -10},
        ]
    )
    assert rows[0]["delta_resultado"] is None
    assert rows[1]["delta_resultado"] == 50
    assert rows[2]["delta_resultado"] is None


def test_missing_discount_column_counts_the_menu_price():
    sales = _sales(
        {
            "Id. Venta": [1],
            "Creación": ["2026-01-10"],
            "Precio": [1000],
            "Creada por": ["uber_eats"],
            "Cantidad": [1],
        }
    )
    rows = monthly_performance(sales, pd.DataFrame())
    assert rows[0]["uber"]["cobrado"] == 1000
    assert rows[0]["uber"]["descuentos"] == 0


@pytest.mark.skipif(not SEP_SALES.exists(), reason="September FUDO file is not in this checkout")
def test_september_uber_collected_matches_the_fudo_payments():
    from simulator.processing.monthly import read_expenses_workbook

    sales = read_sales_workbook(SEP_SALES.read_bytes())
    expenses = read_expenses_workbook(SEP_EXPENSES.read_bytes())
    rows = monthly_performance(sales, expenses)
    september = next(row for row in rows if row["month"] == "2026-09")
    uber = september["uber"]
    assert september["tickets"] == 545
    assert uber["carta"] == 4_272_910
    assert uber["cobrado"] == 2_779_960
    assert uber["comision_neta"] == round(2_779_960 * 0.26)
    assert uber["neto_estimado"] == uber["cobrado"] - uber["tasa_servicio"]
    # September's file has rent and common expenses, and no payroll.
    assert september["sueldos"] == 0
    assert september["pago_gente"] == 0
    assert september["previred"] == 0
    assert september["tiene_remuneraciones"] is False
    assert september["gastos_ops"] > september["uber"]["cobrado"]


@pytest.mark.skipif(not (ROOT / "docs" / "2026" / "gastos").is_dir(), reason="2026 archive missing")
def test_archive_payroll_uses_the_file_and_one_may_previred():
    from simulator.processing.constants import DEFAULT_MONTH_SUELDOS
    from simulator.processing.monthly import load_fudo_archive, people_pay_fallback

    sales, expenses = load_fudo_archive(ROOT / "docs" / "2026")
    rows = {row["month"]: row for row in monthly_performance(sales, expenses)}
    assert rows["2026-05"]["previred"] == 403_711
    assert rows["2026-05"]["pago_gente"] == 1_541_267
    assert rows["2026-02"]["pago_gente"] == 1_954_158
    assert rows["2026-02"]["previred"] == 453_579
    assert rows["2026-06"]["pago_gente"] == 83_000
    assert rows["2026-06"]["previred"] == 138_679
    assert rows["2026-09"]["pago_gente"] == 0
    assert rows["2026-07"]["previred"] == 0
    assert people_pay_fallback(rows["2026-02"]) == 1_954_158
    assert people_pay_fallback(rows["2026-01"]) == rows["2026-01"]["pago_gente"]
    assert people_pay_fallback(rows["2026-06"]) == DEFAULT_MONTH_SUELDOS
    assert people_pay_fallback(rows["2026-09"]) == DEFAULT_MONTH_SUELDOS
    assert "_source" not in expenses.columns
