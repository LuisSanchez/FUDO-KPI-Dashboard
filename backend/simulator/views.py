import pandas as pd
import numpy as np
import io
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache

from .data_processing import (
    sales_clean_up_data,
    kpi_calculations,
    validate_sales_columns,
    validate_expenses_columns,
    get_unique_products,
    get_sales_table,
    get_expenses_table,
    get_chart_data,
)


# In-memory storage for uploaded data (in production, use a proper database)
_session_data = {
    "sales_df": None,
    "expenses_df": None,
    "products": [],
}


@api_view(["POST"])
def upload_sales(request):
    """Upload and validate sales Excel file."""
    if "file" not in request.FILES:
        return Response(
            {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
        )

    file = request.FILES["file"]

    # Check file extension
    if not (file.name.endswith(".xlsx") or file.name.endswith(".xls")):
        return Response(
            {"error": "File must be an Excel file (.xlsx or .xls)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Read the Excel file
        df = pd.read_excel(io.BytesIO(file.read()), sheet_name="Adiciones")

        # Filter cancelled line items before any processing
        if "Cancelada" in df.columns:
            df = df[df["Cancelada"] == "No"].copy()

        # Validate columns
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

        # Clean the data
        df_clean = sales_clean_up_data(df=df)

        # Store in session
        _session_data["sales_df"] = df_clean
        _session_data["products"] = get_unique_products(df=df_clean)

        months = sorted(
            df_clean["created_at"]
            .dt.to_period("M")
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        return Response(
            {
                "message": "Sales file uploaded successfully",
                "products": _session_data["products"],
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

    # Check file extension
    if not (file.name.endswith(".xlsx") or file.name.endswith(".xls")):
        return Response(
            {"error": "File must be an Excel file (.xlsx or .xls)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Read the Excel file
        df = pd.read_excel(io.BytesIO(file.read()), sheet_name="Gastos", skiprows=3)

        # Validate columns
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

        # Store in session
        _session_data["expenses_df"] = df

        return Response(
            {
                "message": "Expenses file uploaded successfully",
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
    if _session_data["sales_df"] is None:
        return Response(
            {"error": "No sales data uploaded yet"}, status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        {
            "products": _session_data["products"],
        }
    )


@api_view(["POST"])
def calculate(request):
    """Calculate KPIs with simulated sales."""
    if _session_data["sales_df"] is None:
        return Response(
            {"error": "No sales data uploaded yet"}, status=status.HTTP_400_BAD_REQUEST
        )

    if _session_data["expenses_df"] is None:
        return Response(
            {"error": "No expenses data uploaded yet"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    producto = request.data.get("producto")  # optional
    month = request.data.get("month")  # e.g. "2026-01", optional

    try:
        df_sales = _session_data["sales_df"].copy()
        df_expenses = _session_data["expenses_df"].copy()

        # Filter sales by selected month if provided
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
    if _session_data["sales_df"] is None:
        return Response(
            {"error": "No sales data uploaded yet"}, status=status.HTTP_400_BAD_REQUEST
        )

    month = request.query_params.get("month")
    df = _session_data["sales_df"].copy()
    if month:
        df = df[df["created_at"].dt.to_period("M").astype(str) == month]

    return Response(get_sales_table(df))


@api_view(["GET"])
def expenses_table_data(request):
    """Return individual expense rows for table display."""
    if _session_data["expenses_df"] is None:
        return Response(
            {"error": "No expenses data uploaded yet"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    month = request.query_params.get("month")
    return Response(get_expenses_table(_session_data["expenses_df"], month=month))


@api_view(["GET"])
def chart_data(request):
    """Return all chart datasets for the selected month."""
    if _session_data["sales_df"] is None:
        return Response(
            {"error": "No sales data uploaded yet"}, status=status.HTTP_400_BAD_REQUEST
        )

    month = request.query_params.get("month")
    df = _session_data["sales_df"].copy()
    if month:
        df = df[df["created_at"].dt.to_period("M").astype(str) == month]

    return Response(get_chart_data(df))


@api_view(["POST"])
def reset_data(request):
    """Reset all uploaded data."""
    _session_data["sales_df"] = None
    _session_data["expenses_df"] = None
    _session_data["products"] = []

    return Response({"message": "Data reset successfully"})
