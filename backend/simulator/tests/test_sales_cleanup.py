"""sales_clean_up_data regression tests."""
import pandas as pd

from simulator.data_processing import UBER_COMMISSION_RATE, sales_clean_up_data


def test_cleanup_adds_derived_columns(sample_sales_df):
    df = sales_clean_up_data(sample_sales_df.copy())
    for col in (
        "ingreso",
        "ingreso_sin_iva",
        "comision",
        "margen",
        "margen_sin_iva",
        "costo_ingredientes_sin_iva",
        "created_at",
    ):
        assert col in df.columns


def test_cleanup_iva_factor(sample_sales_df):
    df = sales_clean_up_data(sample_sales_df.copy())
    # ingreso_sin_iva = ingreso / 1.19
    ratio = (df["ingreso_sin_iva"] / df["ingreso"].replace(0, pd.NA)).dropna()
    assert all(abs(r - 1 / 1.19) < 1e-9 for r in ratio)


def test_uber_commission_only_on_uber_rows(sample_sales_df):
    df = sales_clean_up_data(sample_sales_df.copy())
    local = df[df["Creada por"] == "local"]
    uber = df[df["Creada por"] == "uber_eats"]
    assert (local["comision"] == 0).all()
    assert len(uber) == 1
    expected = uber.iloc[0]["ingreso"] * UBER_COMMISSION_RATE
    assert abs(uber.iloc[0]["comision"] - expected) < 1e-6


def test_cleanup_drops_creacion_column(sample_sales_df):
    df = sales_clean_up_data(sample_sales_df.copy())
    assert "Creación" not in df.columns
