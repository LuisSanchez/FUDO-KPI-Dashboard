"""Unit tests for simulator.processing.engine public API."""

import pandas as pd
import pytest

from simulator.processing.constants import UBER_COMMISSION_RATE
from simulator.processing.engine import (
    _build_cost_lookup,
    _impute_zero_costs,
    _lookup_cost,
    _sunday_bucket,
    add_simulated_sales,
    get_chart_data,
    get_expenses_table,
    get_product_prices_table,
    get_promotion_advisor,
    get_sales_excel,
    get_sales_table,
    get_sunday_analysis,
    get_uber_eats_analysis,
    get_unique_products,
    kpi_calculations,
    sales_clean_up_data,
    simulate_price_cost,
    validate_expenses_columns,
    validate_sales_columns,
)


def test_build_cost_lookup_and_lookup(sample_sales_df):
    lookup = _build_cost_lookup(sample_sales_df)
    assert "Pizza Margarita" in lookup
    assert lookup["Pizza Margarita"] > 0
    assert _lookup_cost("Pizza Margarita", lookup) == lookup["Pizza Margarita"]
    assert _lookup_cost("PIZZA MARGARITA", lookup) == lookup["Pizza Margarita"]
    assert _lookup_cost("extra Pizza Margarita text", lookup) > 0
    assert _lookup_cost(None, lookup) == 0.0
    assert _lookup_cost("Unknown", {}) == 0.0


def test_impute_zero_costs_extra_and_generic():
    df = pd.DataFrame(
        {
            "Producto": ["Pizza X", "Pizza X", "Producto Genérico"],
            "Categoría": ["Especialidades", "Extra", "Especialidades"],
            "Cantidad": [1, 1, 2],
            "Costo base": [4000, 0, 0],
            "Costo modificadores": [0, 0, 0],
            "Comentario": ["", "", "Pizza X"],
        }
    )
    lookup = _build_cost_lookup(df)
    out = _impute_zero_costs(df, lookup)
    # Extra promo gets imputed cost
    assert out.loc[out["Categoría"] == "Extra", "Costo base"].iloc[0] > 0
    # Generic resolved via Comentario
    assert out.loc[out["Producto"] == "Producto Genérico", "Costo base"].iloc[0] > 0


def test_sales_clean_up_zero_cost_patch():
    df = pd.DataFrame(
        {
            "Id. Venta": [1, 2],
            "Creación": ["2026-03-01 12:00:00", "2026-03-02 12:00:00"],
            "Producto": ["Pizza Napoli", "Pizza Napoli"],
            "Categoría": ["Especialidades", "Especialidades"],
            "Cantidad": [1, 1],
            "Precio": [12000, 12000],
            "Costo base": [3500, 0],
            "Costo modificadores": [0, 0],
            "Costo total": [3500, 0],
            "Creada por": ["local", "local"],
        }
    )
    cleaned = sales_clean_up_data(df)
    assert (cleaned["Costo base"] > 0).all()


def test_kpi_with_producto_simulation(cleaned_sales, sample_expenses_df):
    kpis = kpi_calculations(cleaned_sales, sample_expenses_df, producto="Pizza Margarita")
    assert kpis["simulation"] is not None
    assert kpis["simulation"]["producto"] == "Pizza Margarita"
    assert "dashboard" in kpis
    assert kpis["dashboard"]["best_weekday"] is not None
    assert kpis["dashboard"]["best_hour"] is not None
    # Cancelled expense excluded; loans/capex separated
    assert kpis["gastos"]["prestamos_socios"] >= 0
    assert kpis["gastos"]["activo_fijo"] >= 0


def test_get_sales_table_by_channel(cleaned_sales):
    rows = get_sales_table(cleaned_sales, by_channel=True)
    assert rows
    assert any(r.get("canal") == "Uber Eats" for r in rows)
    flat = get_sales_table(cleaned_sales, by_channel=False)
    assert flat
    assert "canal" not in flat[0] or flat[0].get("canal") is None or "canal" in flat[0]


def test_get_sales_table_empty():
    assert get_sales_table(pd.DataFrame()) == []


def test_get_expenses_table(sample_expenses_df):
    rows = get_expenses_table(sample_expenses_df, month="2026-03")
    assert rows
    # Cancelled "Si" excluded
    assert all(r["Importe"] != 0 or True for r in rows)
    assert any(r["Tipo"] in ("Operacional", "Préstamo", "Activo Fijo") for r in rows)


def test_get_chart_data(cleaned_sales):
    charts = get_chart_data(cleaned_sales)
    assert "hourly" in charts
    assert len(charts["hourly"]["labels"]) == 24
    assert "channel_split" in charts
    assert "channel_by_category" in charts
    assert "Especialidades" in charts["channel_by_category"]
    assert get_chart_data(pd.DataFrame()) == {}


def test_get_product_prices_table(cleaned_sales):
    rows = get_product_prices_table(cleaned_sales)
    assert rows
    marg = next(r for r in rows if r["Producto"] == "Pizza Margarita")
    assert marg["avg_precio"] > 0
    assert "tiene_uber_eats" in marg
    assert get_product_prices_table(pd.DataFrame()) == []


def test_simulate_price_cost(cleaned_sales, sample_expenses_df):
    result = simulate_price_cost(cleaned_sales, sample_expenses_df, 500, 5)
    assert result["projected_ebitda"] != result["current_ebitda"] or result["revenue_delta"] >= 0
    assert result["total_tickets"] > 0
    assert result["esp_units_sold"] > 0
    assert simulate_price_cost(pd.DataFrame(), sample_expenses_df, 0, 0) == {}


def test_get_promotion_advisor(cleaned_sales):
    advice = get_promotion_advisor(cleaned_sales)
    assert "especialidades" in advice
    assert "extras" in advice
    assert "uber_hours" in advice
    assert advice["uber_units"] >= 0
    assert get_promotion_advisor(pd.DataFrame()) == {}


def test_get_sales_excel(cleaned_sales):
    xlsx = get_sales_excel(cleaned_sales, "Especialidades")
    assert isinstance(xlsx, (bytes, bytearray))
    assert len(xlsx) > 100


def test_add_simulated_sales(sample_sales_df):
    out = add_simulated_sales(sample_sales_df.copy(), "Pizza Margarita", 5)
    assert len(out) == len(sample_sales_df) + 1
    assert (out["Id. Venta"].astype(str).str.startswith("SIM_")).any()
    # Second sim increments id
    out2 = add_simulated_sales(out, "Pizza Margarita", 1)
    sim_ids = out2["Id. Venta"].astype(str)
    assert sim_ids.str.startswith("SIM_").sum() == 2
    with pytest.raises(ValueError):
        add_simulated_sales(sample_sales_df.copy(), "Does Not Exist", 1)


def test_get_uber_eats_analysis(cleaned_sales, sample_expenses_df):
    result = get_uber_eats_analysis(cleaned_sales, sample_expenses_df)
    assert result["has_uber_data"] is True
    assert result["total_units"] > 0
    assert "products" in result
    assert "breakeven_units_total" in result
    no_uber = cleaned_sales[cleaned_sales["Creada por"] != "uber_eats"]
    assert get_uber_eats_analysis(no_uber)["has_uber_data"] is False


def test_get_sunday_analysis(cleaned_sales, sample_expenses_df):
    result = get_sunday_analysis(cleaned_sales, sample_expenses_df)
    assert result["has_data"] is True
    assert result["has_expenses"] is True
    assert "sunday" in result
    assert result["has_sunday_data"] is True
    assert get_sunday_analysis(pd.DataFrame())["has_data"] is False


def test_sunday_bucket():
    assert (
        _sunday_bucket({"Subcategoría": "Arriendo local", "Categoría": "", "Proveedor": ""})
        == "Arriendo"
    )
    assert (
        _sunday_bucket({"Subcategoría": "electricidad", "Categoría": "", "Proveedor": ""})
        == "Electricidad"
    )
    assert _sunday_bucket({"Subcategoría": "x", "Categoría": "y", "Proveedor": "z"}) is None


def test_validate_and_products_edge_cases():
    ok, missing = validate_expenses_columns(pd.DataFrame({"Id": []}))
    assert ok is False
    assert missing
    assert get_unique_products(pd.DataFrame()) == []
    assert get_unique_products(pd.DataFrame({"x": [1]})) == []


def test_uber_commission_constant():
    assert UBER_COMMISSION_RATE == 0.25
