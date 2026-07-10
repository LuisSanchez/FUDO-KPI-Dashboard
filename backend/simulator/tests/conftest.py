import pandas as pd
import pytest


@pytest.fixture
def sample_sales_df():
    """Minimal sales rows covering local + Uber Eats + both categories."""
    return pd.DataFrame(
        {
            "Id. Venta": [1, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            "Creación": [
                "2026-03-01 12:00:00",
                "2026-03-01 12:00:00",
                "2026-03-02 18:00:00",
                "2026-03-03 20:00:00",
                "2026-03-08 13:00:00",  # Sunday
                "2026-03-08 14:00:00",  # Sunday
                "2026-03-09 19:00:00",
                "2026-03-10 12:00:00",
                "2026-03-11 18:00:00",
                "2026-03-12 20:00:00",
            ],
            "Producto": [
                "Pizza Margarita",
                "Bebida",
                "Pizza Napoli",
                "Pizza Margarita",
                "Pizza Margarita",
                "Bebida",
                "Pizza Napoli",
                "Pizza Margarita",
                "Pizza Napoli",
                "Bebida",
            ],
            "Categoría": [
                "Especialidades",
                "Extras",
                "Especialidades",
                "Especialidades",
                "Especialidades",
                "Extras",
                "Especialidades",
                "Especialidades",
                "Especialidades",
                "Extras",
            ],
            "Cantidad": [2, 3, 2, 2, 3, 2, 2, 2, 2, 3],
            "Precio": [20000, 6000, 24000, 20000, 30000, 4000, 24000, 20000, 24000, 6000],
            "Costo base": [6000, 1500, 7000, 6000, 9000, 1000, 7000, 6000, 7000, 1500],
            "Costo modificadores": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "Costo total": [6000, 1500, 7000, 6000, 9000, 1000, 7000, 6000, 7000, 1500],
            "Creada por": [
                "local",
                "local",
                "uber_eats",
                "local",
                "local",
                "uber_eats",
                "uber_eats",
                "local",
                "local",
                "local",
            ],
            "Comentario": [""] * 10,
        }
    )


@pytest.fixture
def sample_expenses_df():
    return pd.DataFrame(
        {
            "Id": [1, 2, 3, 4, 5],
            "Fecha": [
                "2026-03-01",
                "2026-03-15",
                "2026-03-05",
                "2026-03-10",
                "2026-03-12",
            ],
            "Fecha de vencimiento": [
                "2026-03-10",
                "2026-03-20",
                "2026-03-15",
                "2026-03-20",
                "2026-03-25",
            ],
            "Proveedor": ["A", "B", "Prestamo Socios", "Capex SA", "C"],
            "Categoría": [
                "Operacional",
                "Operacional",
                "Operacional",
                "Activo Fijo",
                "Operacional",
            ],
            "Subcategoría": ["Arriendo", "Electricidad", "Financiamiento", "Equipo", "Personal"],
            "Comentario": ["", "", "", "", ""],
            "Estado del pago": ["Pagado", "A pagar", "Pagado", "Pagado", "Pagado"],
            "Importe": [200000, 50000, 100000, 80000, 150000],
            "Número Fiscal": ["1", "2", "3", "4", "5"],
            "Tipo de comprobante": ["Factura"] * 5,
            "N° de comprobante": ["1", "2", "3", "4", "5"],
            "Creado por": ["admin"] * 5,
            "Cancelado": ["No", "No", "No", "No", "Si"],
        }
    )


@pytest.fixture
def cleaned_sales(sample_sales_df):
    from simulator.data_processing import sales_clean_up_data

    return sales_clean_up_data(sample_sales_df.copy())


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def seeded_store(api_client, cleaned_sales, sample_expenses_df):
    """Session store with sales + expenses already pickled (no Excel I/O)."""
    from simulator.models import UserSessionData
    from simulator.services.session_store import dump_df

    session = api_client.session
    session.save()
    store, _ = UserSessionData.objects.get_or_create(session_key=session.session_key)
    store.sales_df_pickle = dump_df(cleaned_sales)
    store.expenses_df_pickle = dump_df(sample_expenses_df)
    store.products = sorted(cleaned_sales["Producto"].unique().tolist())
    store.sales_months = sorted(
        cleaned_sales["created_at"].dt.to_period("M").astype(str).unique().tolist()
    )
    store.save()
    return store
