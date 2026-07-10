import pandas as pd

from simulator.data_processing import (
    get_unique_products,
    validate_expenses_columns,
    validate_sales_columns,
)


def test_validate_sales_columns_ok(sample_sales_df):
    ok, missing = validate_sales_columns(sample_sales_df)
    assert ok is True
    assert missing == []


def test_validate_sales_columns_missing():
    ok, missing = validate_sales_columns(pd.DataFrame({"Producto": []}))
    assert ok is False
    assert "Id. Venta" in missing


def test_validate_expenses_columns_ok(sample_expenses_df):
    ok, missing = validate_expenses_columns(sample_expenses_df)
    assert ok is True


def test_get_unique_products_sorted(sample_sales_df):
    products = get_unique_products(sample_sales_df)
    assert products == sorted(products)
    assert "Pizza Margarita" in products
