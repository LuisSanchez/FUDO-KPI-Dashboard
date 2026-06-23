from typing import Dict, Any, Optional

import pandas as pd

from .constants import UBER_COMMISSION_RATE

def get_uber_eats_analysis(
    df_sales: pd.DataFrame, df_expenses: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Analyse Uber Eats performance:
    - Per-product margin after 25% commission (net of IVA).
    - Summary totals: units, revenue, ingredient cost, commission, margin.
    - Break-even in units (total and per day) using operational fixed costs when
      expense data is available.
    """
    uber = df_sales[df_sales["Creada por"] == "uber_eats"].copy()

    if uber.empty:
        return {"has_uber_data": False}

    # ── Per-product breakdown ─────────────────────────────────────────────────
    by_prod = (
        uber.groupby(["Producto", "Categoría"])
        .agg(
            cantidad=("Cantidad", "sum"),
            ingreso_sin_iva=("ingreso_sin_iva", "sum"),
            costo_ingredientes=("costo_ingredientes_sin_iva", "sum"),
            comision=("comision", "sum"),
        )
        .reset_index()
    )
    # Commission in the DataFrame is gross (with IVA embedded); net = / 1.19
    by_prod["comision_sin_iva"] = (by_prod["comision"] / 1.19).round(0)
    by_prod["margen_sin_iva"] = (
        by_prod["ingreso_sin_iva"]
        - by_prod["costo_ingredientes"]
        - by_prod["comision_sin_iva"]
    ).round(0)
    by_prod["margen_pct"] = (
        (by_prod["margen_sin_iva"] / by_prod["ingreso_sin_iva"] * 100)
        .where(by_prod["ingreso_sin_iva"] > 0, 0)
        .round(1)
    )
    by_prod = by_prod.sort_values("margen_pct")

    # ── Summary totals ────────────────────────────────────────────────────────
    total_units = int(uber["Cantidad"].sum())
    total_revenue = float(uber["ingreso_sin_iva"].sum())
    total_ingredient_cost = float(uber["costo_ingredientes_sin_iva"].sum())
    total_commission = float(uber["comision"].sum() / 1.19)
    total_margin = total_revenue - total_ingredient_cost - total_commission
    margin_pct = (total_margin / total_revenue * 100) if total_revenue > 0 else 0

    avg_price = total_revenue / total_units if total_units > 0 else 0
    avg_ingredient = total_ingredient_cost / total_units if total_units > 0 else 0
    avg_commission = total_commission / total_units if total_units > 0 else 0
    avg_contribution = avg_price - avg_ingredient - avg_commission

    date_from = uber["created_at"].min()
    date_to = uber["created_at"].max()
    days = max(1, (date_to - date_from).days + 1)
    units_per_day = total_units / days

    result: Dict[str, Any] = {
        "has_uber_data": True,
        "commission_rate_pct": round(UBER_COMMISSION_RATE * 100, 2),
        "date_from": date_from.strftime("%d/%m/%Y"),
        "date_to": date_to.strftime("%d/%m/%Y"),
        "days_in_period": days,
        "total_units": total_units,
        "total_revenue_sin_iva": round(total_revenue, 0),
        "total_ingredient_cost": round(total_ingredient_cost, 0),
        "total_commission_sin_iva": round(total_commission, 0),
        "total_margin_sin_iva": round(total_margin, 0),
        "margin_pct": round(margin_pct, 1),
        "avg_price_sin_iva": round(avg_price, 0),
        "avg_ingredient_cost_per_unit": round(avg_ingredient, 0),
        "avg_commission_per_unit": round(avg_commission, 0),
        "avg_contribution_per_unit": round(avg_contribution, 0),
        "units_per_day": round(units_per_day, 1),
        "products": [
            {
                "Producto": r["Producto"],
                "Categoría": r["Categoría"],
                "cantidad": int(r["cantidad"]),
                "ingreso_sin_iva": float(r["ingreso_sin_iva"]),
                "costo_ingredientes": float(r["costo_ingredientes"]),
                "comision_sin_iva": float(r["comision_sin_iva"]),
                "margen_sin_iva": float(r["margen_sin_iva"]),
                "margen_pct": float(r["margen_pct"]),
            }
            for _, r in by_prod.iterrows()
        ],
    }

    # ── Break-even (requires expense data) ───────────────────────────────────
    if df_expenses is not None and not df_expenses.empty:
        df_exp = df_expenses[df_expenses["Cancelado"] == "No"].copy()
        sales_months = df_sales["created_at"].dt.to_period("M").unique()
        df_exp["Fecha"] = pd.to_datetime(df_exp["Fecha"], errors="coerce")
        df_exp = df_exp[df_exp["Fecha"].dt.to_period("M").isin(sales_months)]
        is_loan = df_exp["Proveedor"].str.contains("Prestamo", case=False, na=False)
        is_capex = df_exp["Categoría"] == "Activo Fijo"
        fixed_costs = float(df_exp[~is_loan & ~is_capex]["Importe"].sum())

        if avg_contribution > 0:
            breakeven_units = fixed_costs / avg_contribution
            breakeven_per_day = breakeven_units / days
            coverage_pct = (
                min(total_units / breakeven_units * 100, 999)
                if breakeven_units > 0
                else 0
            )
        else:
            breakeven_units = 0
            breakeven_per_day = 0
            coverage_pct = 0

        result["fixed_costs"] = round(fixed_costs, 0)
        result["breakeven_units_total"] = round(breakeven_units, 1)
        result["breakeven_units_per_day"] = round(breakeven_per_day, 1)
        result["coverage_pct"] = round(coverage_pct, 1)

    return result
