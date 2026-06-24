"""Shared fixtures for simulator unit tests."""
import pandas as pd
import pytest


@pytest.fixture
def sample_sales_df():
    """Minimal valid sales rows (local + uber_eats)."""
    return pd.DataFrame(
        {
            "Id. Venta": [1, 1, 2],
            "Creación": ["2026-03-01 12:00:00", "2026-03-01 12:00:00", "2026-03-02 18:00:00"],
            "Producto": ["Pizza Margherita", "Bebida Cola", "Pizza Napoli"],
            "Categoría": ["Especialidades", "Extras", "Especialidades"],
            "Cantidad": [1, 2, 1],
            "Precio": [11900, 2000, 12900],
            "Costo base": [3000, 500, 3500],
            "Costo modificadores": [0, 0, 0],
            "Costo total": [3000, 500, 3500],
            "Creada por": ["local", "local", "uber_eats"],
        }
    )


@pytest.fixture
def sample_expenses_df():
    """Minimal valid expenses for March 2026."""
    return pd.DataFrame(
        {
            "Id": [1, 2, 3],
            "Fecha": ["2026-03-05", "2026-03-10", "2026-03-15"],
            "Fecha de vencimiento": ["2026-03-05", "2026-03-10", "2026-03-15"],
            "Proveedor": ["Proveedor A", "Prestamo Socio", "Equipo X"],
            "Categoría": ["Materia Prima", "Financiero", "Activo Fijo"],
            "Subcategoría": ["Insumos", "Prestamo", "Equipamiento"],
            "Comentario": ["", "", ""],
            "Estado del pago": ["Pagado", "Pagado", "A pagar"],
            "Importe": [500000, 100000, 200000],
            "Número Fiscal": ["", "", ""],
            "Tipo de comprobante": ["", "", ""],
            "N° de comprobante": ["", "", ""],
            "Creado por": ["admin", "admin", "admin"],
            "Cancelado": ["No", "No", "No"],
        }
    )
