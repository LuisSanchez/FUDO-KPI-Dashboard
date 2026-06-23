from typing import Dict, Any, Optional

import pandas as pd

_SUNDAY_BUCKETS: dict[str, list[str]] = {
    "Arriendo": ["arriendo", "alquiler"],
    "Electricidad": ["electricidad", " luz"],
    "Personal": ["personal", "remuneraci", "sueldo", "rrhh"],
    "GGCC": ["ggcc", "gastos comunes", "gastos comunal", "comunal"],
}

_WEEKDAY_NAMES_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def _sunday_bucket(row) -> Optional[str]:
    text = (
        str(row.get("Subcategoría", ""))
        + " "
        + str(row.get("Categoría", ""))
        + " "
        + str(row.get("Proveedor", ""))
    ).lower()
    for bucket, keywords in _SUNDAY_BUCKETS.items():
        if any(kw in text for kw in keywords):
            return bucket
    return None


def get_sunday_analysis(
    df_sales: pd.DataFrame, df_expenses: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Computes daily break-even analysis to evaluate opening on Sundays.
    Fixed costs considered: Arriendo, Electricidad, Personal, GGCC.
    Returns per-Sunday actual revenue (if any) vs daily fixed cost requirement.
    """
    if df_sales.empty:
        return {"has_data": False}

    df = df_sales.copy()
    df["weekday"] = df["created_at"].dt.dayofweek  # 0=Mon … 6=Sun
    df["_date"] = df["created_at"].dt.date

    date_from = df["_date"].min()
    date_to = df["_date"].max()
    days_in_period = (date_to - date_from).days + 1

    # Overall contribution margin rate (ingredient cost only, ex-IVA)
    total_rev = float(df["ingreso_sin_iva"].sum())
    total_cost_ing = float(df["costo_ingredientes_sin_iva"].sum())
    margin_rate = (total_rev - total_cost_ing) / total_rev if total_rev > 0 else 0.0

    # Per-weekday revenue (Mon=0 … Sun=6)
    wday_rev = (
        df.groupby("weekday")["ingreso_sin_iva"].sum().reindex(range(7), fill_value=0.0)
    )
    wday_days = df.groupby("weekday")["_date"].nunique().reindex(range(7), fill_value=0)

    weekday_avg = [
        (
            round(float(wday_rev[i]) / int(wday_days[i]), 0)
            if int(wday_days[i]) > 0
            else 0.0
        )
        for i in range(7)
    ]

    # Sunday (index 6)
    sun_df = df[df["weekday"] == 6]
    num_sundays = int(sun_df["_date"].nunique())
    has_sunday_data = num_sundays > 0
    sunday_total_rev = float(sun_df["ingreso_sin_iva"].sum())
    avg_sunday_revenue = sunday_total_rev / num_sundays if num_sundays > 0 else 0.0
    sunday_tickets = int(sun_df["Id. Venta"].nunique())
    avg_sunday_tickets = sunday_tickets / num_sundays if num_sundays > 0 else 0.0
    avg_sunday_contribution = avg_sunday_revenue * margin_rate

    result: Dict[str, Any] = {
        "has_data": True,
        "has_expenses": False,
        "has_sunday_data": has_sunday_data,
        "date_from": str(date_from),
        "date_to": str(date_to),
        "days_in_period": days_in_period,
        "margin_rate_pct": round(margin_rate * 100, 1),
        "weekday_avg_revenue": {
            "labels": _WEEKDAY_NAMES_ES,
            "values": weekday_avg,
        },
        "sunday": {
            "num_sundays": num_sundays,
            "total_revenue": round(sunday_total_rev, 0),
            "avg_revenue": round(avg_sunday_revenue, 0),
            "total_tickets": sunday_tickets,
            "avg_tickets": round(avg_sunday_tickets, 1),
            "avg_contribution": round(avg_sunday_contribution, 0),
        },
    }

    if df_expenses is not None and not df_expenses.empty:
        df_exp = df_expenses[df_expenses["Cancelado"] == "No"].copy()
        df_exp["Fecha"] = pd.to_datetime(df_exp["Fecha"], errors="coerce")
        sales_months = df["created_at"].dt.to_period("M").unique()
        df_exp = df_exp[df_exp["Fecha"].dt.to_period("M").isin(sales_months)]

        is_loan = df_exp["Proveedor"].str.contains("Prestamo", case=False, na=False)
        is_capex = df_exp["Categoría"] == "Activo Fijo"
        df_ops = df_exp[~is_loan & ~is_capex].copy()

        df_ops["_bucket"] = df_ops.apply(_sunday_bucket, axis=1)
        df_match = df_ops[df_ops["_bucket"].notna()]

        fixed_total = float(df_match["Importe"].sum())
        breakdown = (
            df_match.groupby("_bucket")["Importe"]
            .sum()
            .reset_index()
            .sort_values("Importe", ascending=False)
        )
        daily_fixed = fixed_total / days_in_period if days_in_period > 0 else 0.0
        needed_revenue = daily_fixed / margin_rate if margin_rate > 0 else 0.0
        coverage_pct = (
            avg_sunday_revenue / needed_revenue * 100
            if needed_revenue > 0 and has_sunday_data
            else 0.0
        )

        result["has_expenses"] = True
        result["fixed_costs"] = {
            "total": round(fixed_total, 0),
            "daily": round(daily_fixed, 0),
            "breakdown": [
                {"label": str(r["_bucket"]), "total": round(float(r["Importe"]), 0)}
                for _, r in breakdown.iterrows()
            ],
        }
        result["needed_revenue"] = round(needed_revenue, 0)
        result["coverage_pct"] = round(coverage_pct, 1)
        result["sunday"]["is_viable"] = avg_sunday_contribution >= daily_fixed

    return result
