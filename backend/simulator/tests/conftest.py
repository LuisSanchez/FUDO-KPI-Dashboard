import pytest
import pandas as pd


@pytest.fixture
def sample_sales_df():
    return pd.DataFrame(
        {
            "Id. Venta": [1, 1, 2, 3],
            "Creación": [
                "2026-03-01 12:00:00",
                "2026-03-01 12:00:00",
                "2026-03-02 18:00:00",
                "2026-03-03 20:00:00",
            ],
            "Producto": ["Pizza Margarita", "Bebida", "Pizza Napoli", "Pizza Margarita"],
            "Categoría": ["Especialidades", "Extras", "Especialidades", "Especialidades"],
            "Cantidad": [1, 2, 1, 1],
            "Precio": [10000, 2000, 12000, 10000],
            "Costo base": [3000, 500, 3500, 3000],
            "Costo modificadores": [0, 0, 0, 0],
            "Costo total": [3000, 500, 3500, 3000],
            "Creada por": ["local", "local", "uber_eats", "local"],
        }
    )


@pytest.fixture
def sample_expenses_df():
    return pd.DataFrame(
        {
            "Id": [1, 2],
            "Fecha": ["2026-03-01", "2026-03-15"],
            "Fecha de vencimiento": ["2026-03-10", "2026-03-20"],
            "Proveedor": ["A", "B"],
            "Categoría": ["Operacional", "Operacional"],
            "Subcategoría": ["Arriendo", "Servicios"],
            "Comentario": ["", ""],
            "Estado del pago": ["Pagado", "Pendiente"],
            "Importe": [500000, 100000],
            "Número Fiscal": ["1", "2"],
            "Tipo de comprobante": ["Factura", "Boleta"],
            "N° de comprobante": ["1", "2"],
            "Creado por": ["admin", "admin"],
            "Cancelado": ["No", "No"],
            "Tipo": ["Operacional", "Operacional"],
        }
    )


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()
