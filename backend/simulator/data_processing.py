import pandas as pd
import io
from typing import Dict, Any, List


def sales_clean_up_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean up sales dataframe and calculate margins."""
    # this will asume that the columns are in the correct format, if not, it will raise an error
    if "Creación" in df.columns:
        skipped_columns = [
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
        df = df[skipped_columns].copy()

    # if Producto column is 'Duo Familiar (2pizzas)' set Costo modificadores to 0
    df.loc[df["Producto"] == "Duo Familiar (2pizzas)", "Costo modificadores"] = 0

    df["precio_unitario"] = df["Precio"] / df["Cantidad"]
    df["costo_unitario"] = df["Costo base"] / df["Cantidad"]
    df["ingreso"] = df["precio_unitario"] * df["Cantidad"]

    df["comision"] = 0.0
    df.loc[df["Creada por"] == "uber_eats", "comision"] = df["ingreso"] * 0.30

    df["Costo total"] = (df["costo_unitario"] * df["Cantidad"]) + df["Costo modificadores"] + df["comision"]

    df["ingreso"] = df["ingreso"].fillna(0).astype(float)
    df["ingreso_sin_iva"] = df["ingreso"] / 1.19
    df["costo_sin_iva"] = df["Costo total"] / 1.19

    df["margen"] = df["ingreso"] - df["Costo total"]

    df["margen_sin_iva"] = df["ingreso_sin_iva"] - df["costo_sin_iva"]

    df["created_at"] = pd.to_datetime(df["Creación"], errors='coerce')

    df.drop(columns=["Creación"], inplace=True)
    df.sort_values(by="created_at", inplace=True)

    return df


def kpi_calculations(df: pd.DataFrame, df_expenses: pd.DataFrame, sueldos: float = 0) -> Dict[str, Any]:
    """Calculate KPIs for the simulator."""
    total_margen = df["margen"].sum()
    total_ingreso = df["ingreso"].sum()
    total_ingreso_sin_iva = df["ingreso_sin_iva"].sum()
    comision_total = df["comision"].sum()
    costo_total = df["Costo total"].sum()
    costo_sin_iva = df["costo_sin_iva"].sum()
    total_margen_sin_iva = df["margen_sin_iva"].sum()

    # Filter cancelled expenses
    df_expenses = df_expenses[df_expenses["Cancelado"] == "No"].copy()

    # Filter expenses to months present in the sales data
    sales_months = df["created_at"].dt.to_period("M").unique()
    df_expenses["Fecha"] = pd.to_datetime(df_expenses["Fecha"], errors="coerce")
    df_expenses = df_expenses[df_expenses["Fecha"].dt.to_period("M").isin(sales_months)]

    # Separate financing and capex from operational expenses
    is_loan = df_expenses["Proveedor"].str.contains("Prestamo", case=False, na=False)
    is_capex = df_expenses["Categoría"] == "Activo Fijo"
    df_ops = df_expenses[~is_loan & ~is_capex]

    gastos_totales = df_ops["Importe"].sum()
    pagados_totales = df_ops[df_ops["Estado del pago"] == "Pagado"]["Importe"].sum()
    por_pagar_totales = df_ops[df_ops["Estado del pago"] == "A pagar"]["Importe"].sum()
    prestamos_socios = df_expenses[is_loan]["Importe"].sum()
    activo_fijo = df_expenses[is_capex]["Importe"].sum()

    ebitda = total_margen_sin_iva - gastos_totales - sueldos
    ebitda_percentage = (ebitda / total_ingreso_sin_iva) * 100 if total_ingreso_sin_iva > 0 else 0

    def r(val):
        return float(round(val, 0))

    return {
        "ingresos": {
            "total_ingreso": r(total_ingreso),
            "total_ingreso_sin_iva": r(total_ingreso_sin_iva),
            "comision_total": r(comision_total),
            "costo_total": r(costo_total),
            "costo_sin_iva": r(costo_sin_iva),
            "total_margen": r(total_margen),
            "total_margen_sin_iva": r(total_margen_sin_iva),
        },
        "gastos": {
            "gastos_totales": r(gastos_totales),
            "pagados_totales": r(pagados_totales),
            "por_pagar_totales": r(por_pagar_totales),
            "prestamos_socios": r(prestamos_socios),
            "activo_fijo": r(activo_fijo),
        },
        "ebitda": {
            "ebitda": r(ebitda),
            "ebitda_percentage": float(round(ebitda_percentage, 2)),
        }
    }


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


def add_simulated_sales(df: pd.DataFrame, producto: str, cantidad: int) -> pd.DataFrame:
    """Add simulated sales to the dataframe.
    
    Adds only 1 row with the specified quantity.
    Other calculations (precio_unitario, costo_unitario, etc.) are done in sales_clean_up_data.
    """
    # Get the last row with the selected product to use as template
    product_rows = df[df["Producto"] == producto]
    
    if product_rows.empty:
        raise ValueError(f"Producto '{producto}' no encontrado en los datos")
    
    # Use the first occurrence as template
    template = product_rows.iloc[0].copy()
    
    # Get the last Id. Venta and increment by 1
    # Extract numeric parts from existing SIM ids or use the length
    existing_ids = df["Id. Venta"].astype(str)
    sim_ids = existing_ids[existing_ids.str.startswith("SIM_")]
    
    if not sim_ids.empty:
        # Get the max numeric part from SIM ids
        max_sim_num = sim_ids.str.replace("SIM_", "").astype(int).max()
        new_id = f"SIM_{max_sim_num + 1}"
    else:
        # Start from 1 if no SIM ids exist
        new_id = f"SIM_1"
    
    # Create single new row with the specified quantity
    new_row = template.copy()
    new_row["Id. Venta"] = new_id
    new_row["Cantidad"] = cantidad  # Use the input quantity
    new_row["Creación"] = pd.Timestamp.now()
    
    # Append new row to dataframe
    new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    # Recalculate the cleanup
    new_df = sales_clean_up_data(new_df)
    
    return new_df
