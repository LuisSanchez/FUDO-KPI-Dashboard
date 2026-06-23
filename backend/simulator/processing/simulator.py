from typing import Dict, Any

import pandas as pd

from .cleaning import sales_clean_up_data

def simulate_price_cost(
    df: pd.DataFrame,
    df_expenses: pd.DataFrame,
    price_increase_clp: float,
    cost_increase_pct: float,
) -> Dict[str, Any]:
    """
    Simulate the EBITDA impact of two simultaneous changes using the current
    period data as the baseline:

    - price_increase_clp: consumer price increase per unit (CLP con IVA).
      Applied only to Especialidades → extra revenue = esp_units × (price_increase / 1.19).
    - cost_increase_pct: percentage increase on ingredient costs (CMV).
      Applied to total ingredient cost → extra cost = total_cmv × (pct / 100).

    Gastos operacionales (rent, payroll, utilities …) are taken from the expense
    file unmodified; only the variable ingredient component scales.
    """
    if df.empty:
        return {}

    total_units = float(df["Cantidad"].sum())
    total_ingreso_sin_iva = float(df["ingreso_sin_iva"].sum())
    total_costo_ing_sin_iva = float(df["costo_ingredientes_sin_iva"].sum())

    # Price increase applies only to Especialidades
    esp_units = float(df.loc[df["Categoría"] == "Especialidades", "Cantidad"].sum())

    # Replicate the operational expense filter from kpi_calculations
    df_exp = df_expenses[df_expenses["Cancelado"] == "No"].copy()
    sales_months = df["created_at"].dt.to_period("M").unique()
    df_exp["Fecha"] = pd.to_datetime(df_exp["Fecha"], errors="coerce")
    df_exp = df_exp[df_exp["Fecha"].dt.to_period("M").isin(sales_months)]
    is_loan = df_exp["Proveedor"].str.contains("Prestamo", case=False, na=False)
    is_capex = df_exp["Categoría"] == "Activo Fijo"
    gastos_totales = float(df_exp[~is_loan & ~is_capex]["Importe"].sum())

    current_ebitda = total_ingreso_sin_iva - gastos_totales
    current_ebitda_pct = (
        (current_ebitda / total_ingreso_sin_iva * 100)
        if total_ingreso_sin_iva > 0
        else 0
    )

    # Price impact: only Especialidades units earn more (sin IVA)
    revenue_delta = esp_units * (price_increase_clp / 1.19)
    # Cost impact: ingredient costs rise by cost_increase_pct %
    cost_delta = total_costo_ing_sin_iva * (cost_increase_pct / 100)

    projected_ingreso = total_ingreso_sin_iva + revenue_delta
    projected_ebitda = current_ebitda + revenue_delta - cost_delta
    projected_ebitda_pct = (
        (projected_ebitda / projected_ingreso * 100) if projected_ingreso > 0 else 0
    )

    # Average price uses Especialidades units for the price-increase rows
    esp_ingreso_sin_iva = float(
        df.loc[df["Categoría"] == "Especialidades", "ingreso_sin_iva"].sum()
    )
    avg_price_sin_iva = esp_ingreso_sin_iva / esp_units if esp_units > 0 else 0
    avg_price_sin_iva_new = (
        (esp_ingreso_sin_iva + revenue_delta) / esp_units if esp_units > 0 else 0
    )

    total_tickets = int(df["Id. Venta"].nunique()) if "Id. Venta" in df.columns else 0
    avg_ticket_current = (
        total_ingreso_sin_iva / total_tickets if total_tickets > 0 else 0
    )
    avg_ticket_projected = projected_ingreso / total_tickets if total_tickets > 0 else 0
    contribution_pct_current = (
        (total_ingreso_sin_iva - total_costo_ing_sin_iva) / total_ingreso_sin_iva * 100
        if total_ingreso_sin_iva > 0
        else 0
    )
    projected_cmv = total_costo_ing_sin_iva + cost_delta
    contribution_pct_projected = (
        (projected_ingreso - projected_cmv) / projected_ingreso * 100
        if projected_ingreso > 0
        else 0
    )

    date_from = df["created_at"].min().strftime("%d/%m/%Y") if not df.empty else ""
    date_to = df["created_at"].max().strftime("%d/%m/%Y") if not df.empty else ""

    def r(v):
        return float(round(v, 0))

    return {
        "units_sold": int(total_units),
        "esp_units_sold": int(esp_units),
        "total_tickets": total_tickets,
        "date_from": date_from,
        "date_to": date_to,
        "current_ingreso_sin_iva": r(total_ingreso_sin_iva),
        "current_ebitda": r(current_ebitda),
        "current_ebitda_pct": round(current_ebitda_pct, 1),
        "revenue_delta": r(revenue_delta),
        "cost_delta": r(cost_delta),
        "net_delta": r(revenue_delta - cost_delta),
        "projected_ingreso_sin_iva": r(projected_ingreso),
        "projected_ebitda": r(projected_ebitda),
        "projected_ebitda_pct": round(projected_ebitda_pct, 1),
        "avg_price_sin_iva_current": r(avg_price_sin_iva),
        "avg_price_sin_iva_projected": r(avg_price_sin_iva_new),
        "avg_price_clp_current": r(avg_price_sin_iva * 1.19),
        "avg_price_clp_projected": r(avg_price_sin_iva_new * 1.19),
        "cmv_sin_iva_current": r(total_costo_ing_sin_iva),
        "cmv_sin_iva_projected": r(projected_cmv),
        "avg_ticket_current": r(avg_ticket_current),
        "avg_ticket_projected": r(avg_ticket_projected),
        "contribution_pct_current": round(contribution_pct_current, 1),
        "contribution_pct_projected": round(contribution_pct_projected, 1),
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
