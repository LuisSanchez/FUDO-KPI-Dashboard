import pandas as pd
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
    add_simulated_sales,
)


# In-memory storage for uploaded data (in production, use a proper database)
_session_data = {
    'sales_df': None,
    'expenses_df': None,
    'products': [],
}


@api_view(['POST'])
def upload_sales(request):
    """Upload and validate sales Excel file."""
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    file = request.FILES['file']
    
    # Check file extension
    if not (file.name.endswith('.xlsx') or file.name.endswith('.xls')):
        return Response(
            {'error': 'File must be an Excel file (.xlsx or .xls)'},
            status=status.HTTP_400_BAD_REQUEST
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
                    'error': 'Invalid file format',
                    'missing_columns': missing_columns,
                    'available_columns': df.columns.tolist(),
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Clean the data
        df_clean = sales_clean_up_data(df=df)
        
        # Store in session
        _session_data['sales_df'] = df_clean
        _session_data['products'] = get_unique_products(df=df_clean)
        
        return Response({
            'message': 'Sales file uploaded successfully',
            'products': _session_data['products'],
            'total_rows': len(df_clean),
        })
        
    except Exception as e:
        return Response(
            {'error': f'Error processing file: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def upload_expenses(request):
    """Upload and validate expenses Excel file."""
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    file = request.FILES['file']
    
    # Check file extension
    if not (file.name.endswith('.xlsx') or file.name.endswith('.xls')):
        return Response(
            {'error': 'File must be an Excel file (.xlsx or .xls)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Read the Excel file
        df = pd.read_excel(io.BytesIO(file.read()), sheet_name="Gastos", skiprows=3)
        
        # Validate columns
        is_valid, missing_columns = validate_expenses_columns(df)
        
        if not is_valid:
            return Response(
                {
                    'error': 'Invalid file format',
                    'missing_columns': missing_columns,
                    'available_columns': df.columns.tolist(),
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Store in session
        _session_data['expenses_df'] = df
        
        return Response({
            'message': 'Expenses file uploaded successfully',
            'total_rows': len(df),
        })
        
    except Exception as e:
        return Response(
            {'error': f'Error processing file: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_products(request):
    """Get list of available products from uploaded sales data."""
    if _session_data['sales_df'] is None:
        return Response(
            {'error': 'No sales data uploaded yet'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response({
        'products': _session_data['products'],
    })


@api_view(['POST'])
def calculate(request):
    """Calculate KPIs with simulated sales."""
    if _session_data['sales_df'] is None:
        return Response(
            {'error': 'No sales data uploaded yet'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if _session_data['expenses_df'] is None:
        return Response(
            {'error': 'No expenses data uploaded yet'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get parameters
    producto = request.data.get('producto')
    cantidad = request.data.get('cantidad', 0)
    
    if not producto:
        return Response(
            {'error': 'Producto is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        cantidad = int(cantidad)
        if cantidad < 0:
            return Response(
                {'error': 'Cantidad must be a positive number'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except (ValueError, TypeError):
        return Response(
            {'error': 'Cantidad must be a valid number'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get the original sales data
        df_sales = _session_data['sales_df'].copy()
        df_expenses = _session_data['expenses_df'].copy()
        
        # Add simulated sales if quantity > 0
        if cantidad > 0:
            df_sales = add_simulated_sales(df_sales, producto, cantidad)
        
        # Calculate KPIs
        results = kpi_calculations(df_sales, df_expenses)
        
        return Response(results)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Error calculating KPIs: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def reset_data(request):
    """Reset all uploaded data."""
    _session_data['sales_df'] = None
    _session_data['expenses_df'] = None
    _session_data['products'] = []
    
    return Response({'message': 'Data reset successfully'})