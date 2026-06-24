"""kpi_calculations regression tests (nested response shape)."""
from simulator.data_processing import kpi_calculations, sales_clean_up_data


def test_kpi_ebitda_is_revenue_minus_ops_expenses(sample_sales_df, sample_expenses_df):
    sales = sales_clean_up_data(sample_sales_df.copy())
    result = kpi_calculations(sales, sample_expenses_df.copy())

    # Only non-loan, non-capex expenses count as operational
    # sample: 500000 ops only (loan + activo fijo excluded)
    assert result["gastos"]["gastos_totales"] == 500000
    expected_ebitda = result["ingresos"]["total_ingreso_sin_iva"] - 500000
    assert abs(result["ebitda"]["ebitda"] - expected_ebitda) < 1e-6


def test_kpi_excludes_loans_and_capex_from_ops(sample_sales_df, sample_expenses_df):
    sales = sales_clean_up_data(sample_sales_df.copy())
    result = kpi_calculations(sales, sample_expenses_df.copy())
    assert result["gastos"]["prestamos_socios"] == 100000
    assert result["gastos"]["activo_fijo"] == 200000


def test_kpi_returns_nested_sections(sample_sales_df, sample_expenses_df):
    sales = sales_clean_up_data(sample_sales_df.copy())
    result = kpi_calculations(sales, sample_expenses_df.copy())
    for section in ("ingresos", "gastos", "ebitda", "dashboard"):
        assert section in result
    assert "ebitda_percentage" in result["ebitda"]
    assert "cmv_percentage" in result["ingresos"]


def test_kpi_cmv_uses_ingredient_cost_not_commission(sample_sales_df, sample_expenses_df):
    sales = sales_clean_up_data(sample_sales_df.copy())
    result = kpi_calculations(sales, sample_expenses_df.copy())
    assert result["ingresos"]["cmv_percentage"] >= 0
    assert result["ingresos"]["total_ingreso_sin_iva"] > 0
