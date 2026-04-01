import io
import pickle

import pandas as pd
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import UserSessionData
from .data_processing import (
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
    get_sales_excel,
    get_promotion_advisor,
)


# ── Session helpers ────────────────────────────────────────────────────────────


def _get_store(request) -> UserSessionData:
    """Return (or create) the UserSessionData row for the current browser session."""
    if not request.session.session_key:
        request.session.create()
    store, _ = UserSessionData.objects.get_or_create(
        session_key=request.session.session_key
    )
    return store


def _load_df(blob) -> pd.DataFrame:
    """Deserialize a pickled DataFrame from a BinaryField value."""
    if blob is None:
        return pd.DataFrame()
    return pickle.loads(bytes(blob))


def _dump_df(df: pd.DataFrame | None) -> bytes | None:
    """Serialize a DataFrame to bytes for BinaryField storage."""
    if df is None:
        return None
    return pickle.dumps(df)


# ── Endpoints ─────────────────────────────────────────────────────────────────


@api_view(["POST"])
def upload_sales(request):
    """Upload and validate sales Excel file."""
    if "file" not in request.FILES:
        return Response(
            {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
        )

    file = request.FILES["file"]

    if not (file.name.endswith(".xlsx") or file.name.endswith(".xls")):
        return Response(
            {"error": "File must be an Excel file (.xlsx or .xls)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        df = pd.read_excel(io.BytesIO(file.read()), sheet_name="Adiciones")

        if "Cancelada" in df.columns:
            df = df[df["Cancelada"] == "No"].copy()

        is_valid, missing_columns = validate_sales_columns(df)
        if not is_valid:
            return Response(
                {
                    "error": "Invalid file format",
                    "missing_columns": missing_columns,
                    "available_columns": df.columns.tolist(),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        df_clean = sales_clean_up_data(df=df)
        months = sorted(
            df_clean["created_at"]
            .dt.to_period("M")
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        products = get_unique_products(df=df_clean)

        store = _get_store(request)
        store.sales_df_pickle = _dump_df(df_clean)
        store.expenses_df_pickle = None  # require re-upload of expenses
        store.products = products
        store.sales_months = months
        store.save()

        return Response(
            {
                "message": "Sales file uploaded successfully",
                "products": products,
                "months": months,
                "total_rows": len(df_clean),
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Error processing file: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def upload_expenses(request):
    """Upload and validate expenses Excel file."""
    if "file" not in request.FILES:
        return Response(
            {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
        )

    file = request.FILES["file"]

    if not (file.name.endswith(".xlsx") or file.name.endswith(".xls")):
        return Response(
            {"error": "File must be an Excel file (.xlsx or .xls)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        df = pd.read_excel(io.BytesIO(file.read()), sheet_name="Gastos", skiprows=3)

        is_valid, missing_columns = validate_expenses_columns(df)
        if not is_valid:
            return Response(
                {
                    "error": "Invalid file format",
                    "missing_columns": missing_columns,
                    "available_columns": df.columns.tolist(),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        expense_months = sorted(
            df["Fecha"].dropna().dt.to_period("M").astype(str).unique().tolist()
        )

        store = _get_store(request)
        sales_months = store.sales_months or []

        if sales_months:
            overlap = set(expense_months) & set(sales_months)
            if not overlap:
                return Response(
                    {
                        "error": "date_mismatch",
                        "sales_months": sales_months,
                        "expense_months": expense_months,
                    },
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
            df = df[df["Fecha"].dt.to_period("M").astype(str).isin(overlap)]
            expense_months = sorted(
                df["Fecha"].dropna().dt.to_period("M").astype(str).unique().tolist()
            )

        store.expenses_df_pickle = _dump_df(df)
        store.save()

        return Response(
            {
                "message": "Expenses file uploaded successfully",
                "expense_months": expense_months,
                "total_rows": len(df),
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Error processing file: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def get_products(request):
    """Get list of available products from uploaded sales data."""
    store = _get_store(request)
    if store.sales_df_pickle is None:
        return Response(
            {"error": "No sales data uploaded yet"}, status=status.HTTP_400_BAD_REQUEST
        )
    return Response({"products": store.products})


@api_view(["POST"])
def calculate(request):
    """Calculate KPIs with optional product/month filter."""
    store = _get_store(request)
    if store.sales_df_pickle is None:
        return Response(
            {"error": "No sales data uploaded yet"}, status=status.HTTP_400_BAD_REQUEST
        )
    if store.expenses_df_pickle is None:
        return Response(
            {"error": "No expenses data uploaded yet"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    producto = request.data.get("producto")
    month = request.data.get("month")

    try:
        df_sales = _load_df(store.sales_df_pickle).copy()
        df_expenses = _load_df(store.expenses_df_pickle).copy()

        if month:
            df_sales = df_sales[
                df_sales["created_at"].dt.to_period("M").astype(str) == month
            ]

        results = kpi_calculations(df_sales, df_expenses, producto=producto)
        return Response(results)

    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {"error": f"Error calculating KPIs: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def sales_table_data(request):
    """Return per-product sales aggregation for table display."""
    store = _get_store(request)
    if store.sales_df_pickle is None:
        return Response(
            {"error": "No sales data uploaded yet"}, status=status.HTTP_400_BAD_REQUEST
        )

    month = request.query_params.get("month")
    df = _load_df(store.sales_df_pickle).copy()
    if month:
        df = df[df["created_at"].dt.to_period("M").astype(str) == month]

    return Response(get_sales_table(df))


@api_view(["GET"])
def expenses_table_data(request):
    """Return individual expense rows for table display."""
    store = _get_store(request)
    if store.expenses_df_pickle is None:
        return Response(
            {"error": "No expenses data uploaded yet"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    month = request.query_params.get("month")
    return Response(get_expenses_table(_load_df(store.expenses_df_pickle), month=month))


@api_view(["GET"])
def chart_data(request):
    """Return all chart datasets for the selected month."""
    store = _get_store(request)
    if store.sales_df_pickle is None:
        return Response(
            {"error": "No sales data uploaded yet"}, status=status.HTTP_400_BAD_REQUEST
        )

    month = request.query_params.get("month")
    df = _load_df(store.sales_df_pickle).copy()
    if month:
        df = df[df["created_at"].dt.to_period("M").astype(str) == month]

    return Response(get_chart_data(df))


@api_view(["GET"])
def product_prices_data(request):
    """Return per-product average pricing and raw margin breakdown."""
    store = _get_store(request)
    if store.sales_df_pickle is None:
        return Response(
            {"error": "No sales data uploaded yet"}, status=status.HTTP_400_BAD_REQUEST
        )

    month = request.query_params.get("month")
    df = _load_df(store.sales_df_pickle).copy()
    if month:
        df = df[df["created_at"].dt.to_period("M").astype(str) == month]

    return Response(get_product_prices_table(df))


@api_view(["GET"])
def price_cost_simulator(request):
    """
    Simulate the EBITDA impact of a price increase per unit (CLP con IVA)
    and a percentage increase in ingredient costs.

    Query params:
      price_increase  — CLP con IVA added to every pizza sold (default 0)
      cost_increase   — % increase on ingredient costs (default 0)
      month           — optional YYYY-MM filter
    """
    store = _get_store(request)
    if store.sales_df_pickle is None:
        return Response(
            {"error": "No sales data uploaded yet"}, status=status.HTTP_400_BAD_REQUEST
        )
    if store.expenses_df_pickle is None:
        return Response(
            {"error": "No expenses data uploaded yet"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        price_increase = float(request.query_params.get("price_increase", 0))
        cost_increase = float(request.query_params.get("cost_increase", 0))
        month = request.query_params.get("month")
    except (TypeError, ValueError):
        return Response(
            {"error": "price_increase and cost_increase must be numbers"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        df_sales = _load_df(store.sales_df_pickle).copy()
        df_expenses = _load_df(store.expenses_df_pickle).copy()

        if month:
            df_sales = df_sales[
                df_sales["created_at"].dt.to_period("M").astype(str) == month
            ]

        result = simulate_price_cost(
            df_sales, df_expenses, price_increase, cost_increase
        )
        return Response(result)
    except Exception as e:
        return Response(
            {"error": f"Error running simulation: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def reset_data(request):
    """Reset all uploaded data for this session."""
    store = _get_store(request)
    store.sales_df_pickle = None
    store.expenses_df_pickle = None
    store.products = []
    store.sales_months = []
    store.save()
    return Response({"message": "Data reset successfully"})


@api_view(["GET"])
def download_report(request):
    """Generate and download a PDF financial report for the current session data."""
    from .report import build_financial_report

    store = _get_store(request)
    if store.sales_df_pickle is None:
        return Response(
            {"error": "No sales data uploaded yet"}, status=status.HTTP_400_BAD_REQUEST
        )
    if store.expenses_df_pickle is None:
        return Response(
            {"error": "No expenses data uploaded yet"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    month = request.query_params.get("month")

    try:
        df_sales = _load_df(store.sales_df_pickle).copy()
        df_expenses = _load_df(store.expenses_df_pickle).copy()

        pdf_bytes = build_financial_report(df_sales, df_expenses, month=month)

        filename = f"reporte-{month}.pdf" if month else "reporte-financiero.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        return Response(
            {"error": f"Error generating report: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def download_excel(request):
    """Download an Excel file with all sales calculations for a given category."""
    VALID_CATEGORIES = ["Especialidades", "Extras"]
    categoria = request.query_params.get("categoria", "")
    if categoria not in VALID_CATEGORIES:
        return Response(
            {"error": f"categoria must be one of {VALID_CATEGORIES}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    store = _get_store(request)
    if store.sales_df_pickle is None:
        return Response(
            {"error": "No sales data uploaded yet"}, status=status.HTTP_400_BAD_REQUEST
        )

    month = request.query_params.get("month")

    try:
        df_sales = _load_df(store.sales_df_pickle).copy()
        if month:
            df_sales = df_sales[
                df_sales["created_at"].dt.to_period("M").astype(str) == month
            ]

        xlsx_bytes = get_sales_excel(df_sales, categoria)

        suffix = f"-{month}" if month else ""
        filename = f"ventas-{categoria.lower()}{suffix}.xlsx"
        content_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response = HttpResponse(xlsx_bytes, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        return Response(
            {"error": f"Error generating Excel: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def promotion_advisor(request):
    """Return data-driven promotion recommendations for the current session data."""
    store = _get_store(request)
    if store.sales_df_pickle is None:
        return Response(
            {"error": "No sales data uploaded yet"}, status=status.HTTP_400_BAD_REQUEST
        )

    month = request.query_params.get("month")

    try:
        df_sales = _load_df(store.sales_df_pickle).copy()
        if month:
            df_sales = df_sales[
                df_sales["created_at"].dt.to_period("M").astype(str) == month
            ]
        result = get_promotion_advisor(df_sales)
        return Response(result)
    except Exception as e:
        return Response(
            {"error": f"Error computing advisor: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
