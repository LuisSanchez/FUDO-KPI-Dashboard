from simulator.data_processing import (
    UBER_COMMISSION_RATE,
    kpi_calculations,
    sales_clean_up_data,
)


def test_uber_commission_rate_constant():
    assert UBER_COMMISSION_RATE == 0.25


def test_sales_clean_up_adds_derived_columns(sample_sales_df):
    cleaned = sales_clean_up_data(sample_sales_df.copy())
    for col in (
        "ingreso",
        "ingreso_sin_iva",
        "comision",
        "margen",
        "created_at",
        "costo_ingredientes_sin_iva",
    ):
        assert col in cleaned.columns


def test_uber_row_has_commission(sample_sales_df):
    cleaned = sales_clean_up_data(sample_sales_df.copy())
    uber = cleaned[cleaned["Creada por"] == "uber_eats"]
    assert (uber["comision"] > 0).all()
    local = cleaned[cleaned["Creada por"] == "local"]
    assert (local["comision"] == 0).all()


def test_kpi_ebitda_is_revenue_minus_expenses(sample_sales_df, sample_expenses_df):
    cleaned = sales_clean_up_data(sample_sales_df.copy())
    kpis = kpi_calculations(cleaned, sample_expenses_df)
    assert "ebitda" in kpis
    assert "ebitda" in kpis["ebitda"]
    ebitda = kpis["ebitda"]["ebitda"]
    # EBITDA = net revenue − operational expenses only (exclude loans, capex, cancelled)
    df_exp = sample_expenses_df[sample_expenses_df["Cancelado"] == "No"].copy()
    is_loan = df_exp["Proveedor"].str.contains("Prestamo", case=False, na=False)
    is_capex = df_exp["Categoría"] == "Activo Fijo"
    gastos_ops = float(df_exp[~is_loan & ~is_capex]["Importe"].sum())
    expected = float(cleaned["ingreso_sin_iva"].sum() - gastos_ops)
    assert abs(ebitda - expected) < 1.0
    assert "ingresos" in kpis
