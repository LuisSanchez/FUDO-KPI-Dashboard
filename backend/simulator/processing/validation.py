"""Column validation and simple list helpers."""

from typing import List

import pandas as pd


def validate_sales_columns(df: pd.DataFrame) -> tuple[bool, List[str]]:
    """Validate that the sales dataframe has the required columns."""
    required_columns = [
        "Id. Venta",
        "Creación",
        "Producto",
        "Categoría",
        "Cantidad",
        "Precio",
        "Costo base",
        "Costo modificadores",
        "Costo total",
        "Creada por",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        return False, missing_columns
    return True, []


def validate_expenses_columns(df: pd.DataFrame) -> tuple[bool, List[str]]:
    """Validate that the expenses dataframe has the required columns."""
    required_columns = [
        "Id",
        "Fecha",
        "Fecha de vencimiento",
        "Proveedor",
        "Categoría",
        "Subcategoría",
        "Comentario",
        "Estado del pago",
        "Importe",
        "Número Fiscal",
        "Tipo de comprobante",
        "N° de comprobante",
        "Creado por",
        "Cancelado",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        return False, missing_columns
    return True, []


def get_unique_products(df: pd.DataFrame) -> List[str]:
    """Get list of unique products from sales dataframe."""
    if "Producto" not in df.columns:
        return []

    products = df["Producto"].unique().tolist()
    products.sort()
    return products
