"""KPI and EBITDA calculations."""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

import pandas as pd


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

    df_expenses = df_expenses[df_expenses["Cancelado"] == "No"].copy()

    sales_months = df["created_at"].dt.to_period("M").unique()
    df_expenses["Fecha"] = pd.to_datetime(df_expenses["Fecha"], errors="coerce")
    df_expenses = df_expenses[df_expenses["Fecha"].dt.to_period("M").isin(sales_months)]

    is_loan = df_expenses["Proveedor"].str.contains("Prestamo", case=False, na=False)
    is_capex = df_expenses["Categoría"] == "Activo Fijo"
    df_ops = df_expenses[~is_loan & ~is_capex]

    gastos_totales = df_ops["Importe"].sum()
    pagados_totales = df_ops[df_ops["Estado del pago"] == "Pagado"]["Importe"].sum()
    por_pagar_totales = df_ops[df_ops["Estado del pago"] == "A pagar"]["Importe"].sum()
    prestamos_socios = df_expenses[is_loan]["Importe"].sum()
    activo_fijo = df_expenses[is_capex]["Importe"].sum()

    ebitda = total_ingreso_sin_iva - gastos_totales - sueldos
    ebitda_percentage = (
        (ebitda / total_ingreso_sin_iva) * 100 if total_ingreso_sin_iva > 0 else 0
    )

    def r(val):
        return float(round(val, 0))

    simulation = None
    if producto:
        product_df = df[df["Producto"] == producto]
        if not product_df.empty:
            quantities = product_df["Cantidad"].replace(0, 1)
            avg_ingreso_per_unit = (product_df["ingreso_sin_iva"] / quantities).mean()
            avg_margen_per_unit = (product_df["margen_sin_iva"] / quantities).mean()
            avg_costo_ing_per_unit = (
                product_df["costo_ingredientes_sin_iva"] / quantities
            ).mean()
            avg_contribution_per_unit = avg_ingreso_per_unit - avg_costo_ing_per_unit
            margen_pct = (
                float(round(avg_margen_per_unit / avg_ingreso_per_unit * 100, 1))
                if avg_ingreso_per_unit > 0
                else 0
            )

            already_breakeven = ebitda >= 0
            already_25pct = ebitda_percentage >= 25

            if already_breakeven:
                breakeven_units = 0
            elif avg_contribution_per_unit > 0:
                breakeven_units = math.ceil(-ebitda / avg_contribution_per_unit)
            else:
                breakeven_units = None

            if already_25pct:
                target_25_units = 0
            else:
                denom = avg_contribution_per_unit - 0.25 * avg_ingreso_per_unit
                if denom > 0:
                    numer = 0.25 * total_ingreso_sin_iva - ebitda
                    target_25_units = max(0, math.ceil(numer / denom))
                else:
                    target_25_units = None

            current_units = int(product_df["Cantidad"].sum())
            breakeven_units_int = (
                int(breakeven_units) if breakeven_units is not None else None
            )
            target_25_units_int = (
                int(target_25_units) if target_25_units is not None else None
            )

            simulation = {
                "producto": producto,
                "avg_ingreso_sin_iva_per_unit": r(avg_ingreso_per_unit),
                "avg_margen_sin_iva_per_unit": r(avg_margen_per_unit),
                "margen_pct": margen_pct,
                "current_units": current_units,
                "breakeven_units": breakeven_units_int,
                "target_25_units": target_25_units_int,
                "total_for_breakeven": (
                    current_units + breakeven_units_int
                    if breakeven_units_int is not None
                    else None
                ),
                "total_for_25pct": (
                    current_units + target_25_units_int
                    if target_25_units_int is not None
                    else None
                ),
                "already_breakeven": bool(already_breakeven),
                "already_25pct": bool(already_25pct),
            }

    _WEEKDAY_ES = [
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo",
    ]

    esp_df = df[df["Categoría"] == "Especialidades"]
    esp_units = esp_df["Cantidad"].sum()
    avg_precio_especialidades = (
        float(esp_df["ingreso_sin_iva"].sum() / esp_units) if esp_units > 0 else 0.0
    )

    is_uber = df["Creada por"].str.lower() == "uber_eats"
    df_local = df[~is_uber]
    df_uber = df[is_uber]

    local_rev = df_local["ingreso_sin_iva"].sum()
    local_margin_pct = (
        float(df_local["margen_sin_iva"].sum() / local_rev * 100)
        if local_rev > 0
        else 0.0
    )

    uber_rev = df_uber["ingreso_sin_iva"].sum()
    uber_margin_pct = (
        float(df_uber["margen_sin_iva"].sum() / uber_rev * 100) if uber_rev > 0 else 0.0
    )

    wday_units = df.groupby(df["created_at"].dt.dayofweek)["Cantidad"].sum()
    if not wday_units.empty:
        best_wday_idx = int(wday_units.idxmax())
        best_weekday = {
            "label": _WEEKDAY_ES[best_wday_idx],
            "count": int(wday_units.max()),
        }
    else:
        best_weekday = None

    hour_units = df.groupby(df["created_at"].dt.hour)["Cantidad"].sum()
    if not hour_units.empty:
        best_hour_val = int(hour_units.idxmax())
        best_hour = {
            "label": f"{best_hour_val:02d}:00",
            "count": int(hour_units.max()),
        }
    else:
        best_hour = None

    if not esp_df.empty:
        top_esp_series = esp_df.groupby("Producto")["Cantidad"].sum().nlargest(1)
        top_especialidad = (
            {
                "producto": top_esp_series.index[0],
                "cantidad": int(top_esp_series.iloc[0]),
            }
            if not top_esp_series.empty
            else None
        )
    else:
        top_especialidad = None

    imputation = None
    if "cost_imputed" in df.columns and df["cost_imputed"].any():
        imputation = {
            "imputed_rows": int(df["cost_imputed"].sum()),
            "imputed_units": float(df.loc[df["cost_imputed"], "Cantidad"].sum()),
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
        "dashboard": {
            "avg_precio_especialidades": round(avg_precio_especialidades, 0),
            "local_margin_pct": round(local_margin_pct, 1),
            "uber_margin_pct": round(uber_margin_pct, 1),
            "best_weekday": best_weekday,
            "best_hour": best_hour,
            "top_especialidad": top_especialidad,
        },
        "simulation": simulation,
        "cost_imputation": imputation,
    }
