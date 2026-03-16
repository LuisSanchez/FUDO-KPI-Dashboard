import math
import numpy as np
import pandas as pd
import io
from typing import Dict, Any, List, Optional


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

    df["Costo total"] = (
        (df["costo_unitario"] * df["Cantidad"])
        + df["Costo modificadores"]
        + df["comision"]
    )

    df["ingreso"] = df["ingreso"].fillna(0).astype(float)
    df["ingreso_sin_iva"] = df["ingreso"] / 1.19
    df["costo_sin_iva"] = df["Costo total"] / 1.19
    # CMV: ingredient cost only (excludes commission), net of IVA
    df["costo_ingredientes_sin_iva"] = (df["Costo total"] - df["comision"]) / 1.19

    df["margen"] = df["ingreso"] - df["Costo total"]

    df["margen_sin_iva"] = df["ingreso_sin_iva"] - df["costo_sin_iva"]

    df["created_at"] = pd.to_datetime(df["Creación"], errors="coerce")

    df.drop(columns=["Creación"], inplace=True)
    df.sort_values(by="created_at", inplace=True)

    return df


def kpi_calculations(
    df: pd.DataFrame,
    df_expenses: pd.DataFrame,
    sueldos: float = 0,
    producto: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculate KPIs for the simulator."""
    total_margen = df["margen"].sum()
    total_ingreso = df["ingreso"].sum()
    total_ingreso_sin_iva = df["ingreso_sin_iva"].sum()
    comision_total = df["comision"].sum()
    costo_total = df["Costo total"].sum()
    costo_sin_iva = df["costo_sin_iva"].sum()
    total_margen_sin_iva = df["margen_sin_iva"].sum()
    total_costo_ingredientes_sin_iva = df["costo_ingredientes_sin_iva"].sum()
    cmv_percentage = (
        (total_costo_ingredientes_sin_iva / total_ingreso_sin_iva * 100)
        if total_ingreso_sin_iva > 0
        else 0
    )

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
    ebitda_percentage = (
        (ebitda / total_ingreso_sin_iva) * 100 if total_ingreso_sin_iva > 0 else 0
    )

    def r(val):
        return float(round(val, 0))

    # --- Simulation ---
    simulation = None
    if producto:
        product_df = df[df["Producto"] == producto]
        if not product_df.empty:
            quantities = product_df["Cantidad"].replace(0, 1)
            avg_ingreso_per_unit = (product_df["ingreso_sin_iva"] / quantities).mean()
            avg_margen_per_unit = (product_df["margen_sin_iva"] / quantities).mean()
            margen_pct = (
                float(round(avg_margen_per_unit / avg_ingreso_per_unit * 100, 1))
                if avg_ingreso_per_unit > 0
                else 0
            )

            already_breakeven = total_margen_sin_iva >= gastos_totales
            already_25pct = ebitda_percentage >= 25

            # Breakeven: M + x*m = G  →  x = (G - M) / m
            if already_breakeven:
                breakeven_units = 0
            elif avg_margen_per_unit > 0:
                breakeven_units = math.ceil(
                    (gastos_totales - total_margen_sin_iva) / avg_margen_per_unit
                )
            else:
                breakeven_units = None  # negative or zero margin product

            # 25% EBITDA: (M + x*m - G) / (I + x*i) = 0.25
            # x = (0.25*I + G - M) / (m - 0.25*i)
            if already_25pct:
                target_25_units = 0
            else:
                denom = avg_margen_per_unit - 0.25 * avg_ingreso_per_unit
                if denom > 0:
                    numer = (
                        0.25 * total_ingreso_sin_iva
                        + gastos_totales
                        - total_margen_sin_iva
                    )
                    target_25_units = max(0, math.ceil(numer / denom))
                else:
                    target_25_units = (
                        None  # product margin % too low to ever reach 25% EBITDA
                    )

            simulation = {
                "producto": producto,
                "avg_ingreso_sin_iva_per_unit": r(avg_ingreso_per_unit),
                "avg_margen_sin_iva_per_unit": r(avg_margen_per_unit),
                "margen_pct": margen_pct,
                "breakeven_units": (
                    int(breakeven_units) if breakeven_units is not None else None
                ),
                "target_25_units": (
                    int(target_25_units) if target_25_units is not None else None
                ),
                "already_breakeven": bool(already_breakeven),
                "already_25pct": bool(already_25pct),
            }

    return {
        "ingresos": {
            "total_ingreso": r(total_ingreso),
            "total_ingreso_sin_iva": r(total_ingreso_sin_iva),
            "comision_total": r(comision_total),
            "costo_total": r(costo_total),
            "costo_sin_iva": r(costo_sin_iva),
            "cmv": r(total_costo_ingredientes_sin_iva),
            "cmv_percentage": float(round(cmv_percentage, 2)),
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
        },
        "simulation": simulation,
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


def get_sales_table(df: pd.DataFrame) -> List[Dict]:
    """Aggregate sales by product for table display."""
    if df.empty:
        return []

    grouped = (
        df.groupby(["Producto", "Categoría"])
        .agg(
            cantidad=("Cantidad", "sum"),
            ingreso_sin_iva=("ingreso_sin_iva", "sum"),
            cmv=("costo_ingredientes_sin_iva", "sum"),
            costo_sin_iva=("costo_sin_iva", "sum"),
            margen_sin_iva=("margen_sin_iva", "sum"),
            comision=("comision", "sum"),
        )
        .reset_index()
    )

    grouped["cmv_pct"] = (
        (grouped["cmv"] / grouped["ingreso_sin_iva"] * 100).round(1).fillna(0)
    )
    grouped["margen_pct"] = (
        (grouped["margen_sin_iva"] / grouped["ingreso_sin_iva"] * 100)
        .round(1)
        .fillna(0)
    )

    for col in [
        "ingreso_sin_iva",
        "cmv",
        "costo_sin_iva",
        "margen_sin_iva",
        "comision",
    ]:
        grouped[col] = grouped[col].round(0)

    grouped = grouped.sort_values("ingreso_sin_iva", ascending=False)
    grouped["cmv_pct"] = grouped["cmv_pct"].replace([np.inf, -np.inf], 0)
    grouped["margen_pct"] = grouped["margen_pct"].replace([np.inf, -np.inf], 0)
    return grouped.to_dict(orient="records")


def get_expenses_table(
    df_expenses: pd.DataFrame, month: Optional[str] = None
) -> List[Dict]:
    """Return individual expense rows for table display."""
    df = df_expenses[df_expenses["Cancelado"] == "No"].copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

    if month:
        df = df[df["Fecha"].dt.to_period("M").astype(str) == month]

    is_loan = df["Proveedor"].str.contains("Prestamo", case=False, na=False)
    is_capex = df["Categoría"] == "Activo Fijo"
    df["Tipo"] = "Operacional"
    df.loc[is_loan, "Tipo"] = "Préstamo"
    df.loc[is_capex, "Tipo"] = "Activo Fijo"

    cols = [
        "Fecha",
        "Proveedor",
        "Categoría",
        "Subcategoría",
        "Comentario",
        "Importe",
        "Estado del pago",
        "Tipo",
    ]
    result = df[cols].sort_values("Fecha").copy()
    result["Fecha"] = result["Fecha"].dt.strftime("%Y-%m-%d")
    return result.fillna("").to_dict(orient="records")


def get_chart_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute all chart datasets from a cleaned sales dataframe."""
    if df.empty:
        return {}

    df = df.copy()
    df["hour"] = df["created_at"].dt.hour

    # 1 & 2. Hourly: count of line items and revenue
    hourly_count = df.groupby("hour").size().reindex(range(24), fill_value=0)
    hourly_revenue = (
        df.groupby("hour")["ingreso_sin_iva"]
        .sum()
        .reindex(range(24), fill_value=0)
        .round(0)
    )

    # 3 & 4 & 5 & 6. Per-product aggregation
    by_product = (
        df.groupby("Producto")
        .agg(cantidad=("Cantidad", "sum"), ingreso_sin_iva=("ingreso_sin_iva", "sum"))
        .reset_index()
    )
    by_product["ingreso_sin_iva"] = by_product["ingreso_sin_iva"].round(0)

    top10_qty = by_product.nlargest(10, "cantidad")[["Producto", "cantidad"]].to_dict(
        orient="records"
    )
    top10_rev = by_product.nlargest(10, "ingreso_sin_iva")[
        ["Producto", "ingreso_sin_iva"]
    ].to_dict(orient="records")

    # Pie: top 10 + "Otros"
    top10_pie = by_product.nlargest(10, "cantidad")
    others_qty = float(by_product["cantidad"].sum() - top10_pie["cantidad"].sum())
    pie_labels = top10_pie["Producto"].tolist()
    pie_values = [float(v) for v in top10_pie["cantidad"].tolist()]
    if others_qty > 0:
        pie_labels.append("Otros")
        pie_values.append(others_qty)

    # Scatter: all products (capped at 40 by revenue)
    scatter = by_product.nlargest(40, "ingreso_sin_iva")[
        ["Producto", "cantidad", "ingreso_sin_iva"]
    ].to_dict(orient="records")

    return {
        "hourly": {
            "labels": list(range(24)),
            "count": [int(v) for v in hourly_count.tolist()],
            "revenue": [float(v) for v in hourly_revenue.tolist()],
        },
        "top10_quantity": [
            {"Producto": r["Producto"], "cantidad": float(r["cantidad"])}
            for r in top10_qty
        ],
        "top10_revenue": [
            {"Producto": r["Producto"], "ingreso_sin_iva": float(r["ingreso_sin_iva"])}
            for r in top10_rev
        ],
        "pie_quantity": {"labels": pie_labels, "values": pie_values},
        "scatter": [
            {
                "Producto": r["Producto"],
                "cantidad": float(r["cantidad"]),
                "ingreso_sin_iva": float(r["ingreso_sin_iva"]),
            }
            for r in scatter
        ],
    }


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
