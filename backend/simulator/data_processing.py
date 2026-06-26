"""Public facade for business logic (stable import path for views/tests).

Implementation lives in ``simulator.processing.engine`` for clearer SoC;
this module re-exports the historical API so callers need not change.
"""
from simulator.processing.constants import UBER_COMMISSION_RATE
from simulator.processing.engine import (  # noqa: F401
    sales_clean_up_data,
    kpi_calculations,
    validate_sales_columns,
    validate_expenses_columns,
    get_unique_products,
    get_sales_table,
    get_expenses_table,
    get_chart_data,
    get_product_prices_table,
    simulate_price_cost,
    get_promotion_advisor,
    get_sales_excel,
    add_simulated_sales,
    get_uber_eats_analysis,
    get_sunday_analysis,
)

__all__ = [
    "UBER_COMMISSION_RATE",
    "sales_clean_up_data",
    "kpi_calculations",
    "validate_sales_columns",
    "validate_expenses_columns",
    "get_unique_products",
    "get_sales_table",
    "get_expenses_table",
    "get_chart_data",
    "get_product_prices_table",
    "simulate_price_cost",
    "get_promotion_advisor",
    "get_sales_excel",
    "add_simulated_sales",
    "get_uber_eats_analysis",
    "get_sunday_analysis",
]
