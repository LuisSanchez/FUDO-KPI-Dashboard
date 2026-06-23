"""Business-logic package for sales/expenses analytics.

Public API is re-exported from ``simulator.data_processing`` for backwards
compatibility with views and report modules.
"""

from .constants import UBER_COMMISSION_RATE
from .cleaning import sales_clean_up_data, get_imputation_summary
from .validation import (
    validate_sales_columns,
    validate_expenses_columns,
    get_unique_products,
)
from .kpis import kpi_calculations
from .tables import get_sales_table, get_expenses_table, get_product_prices_table
from .charts import get_chart_data
from .simulator import simulate_price_cost, add_simulated_sales
from .advisor import get_promotion_advisor
from .exports import get_sales_excel
from .uber import get_uber_eats_analysis
from .sunday import get_sunday_analysis

__all__ = [
    "UBER_COMMISSION_RATE",
    "sales_clean_up_data",
    "get_imputation_summary",
    "validate_sales_columns",
    "validate_expenses_columns",
    "get_unique_products",
    "kpi_calculations",
    "get_sales_table",
    "get_expenses_table",
    "get_product_prices_table",
    "get_chart_data",
    "simulate_price_cost",
    "add_simulated_sales",
    "get_promotion_advisor",
    "get_sales_excel",
    "get_uber_eats_analysis",
    "get_sunday_analysis",
]
