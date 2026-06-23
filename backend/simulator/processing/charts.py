import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

def get_chart_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute all chart datasets from a cleaned sales dataframe."""
    if df.empty:
        return {}

    df = df.copy()
    df["hour"] = df["created_at"].dt.hour
    df["day"] = df["created_at"].dt.day
    df["weekday"] = df["created_at"].dt.dayofweek  # 0=Mon … 6=Sun

    # 1 & 2. Hourly: count of line items and revenue
    hourly_count = df.groupby("hour").size().reindex(range(24), fill_value=0)
    hourly_revenue = (
        df.groupby("hour")["ingreso_sin_iva"]
        .sum()
        .reindex(range(24), fill_value=0)
        .round(0)
    )

    # Daily: count of line items and revenue per calendar day
    all_days = range(1, 32)
    daily_count = df.groupby("day").size().reindex(all_days, fill_value=0)
    daily_revenue = (
        df.groupby("day")["ingreso_sin_iva"]
        .sum()
        .reindex(all_days, fill_value=0)
        .round(0)
    )
    # Trim trailing zeros (days beyond the last active day in the data)
    last_active_day = int(df["day"].max()) if not df.empty else 1
    active_days = list(range(1, last_active_day + 1))

    # Weekday: accumulated count and revenue per day-of-week (Mon–Sun)
    weekday_count = df.groupby("weekday").size().reindex(range(7), fill_value=0)
    weekday_revenue = (
        df.groupby("weekday")["ingreso_sin_iva"]
        .sum()
        .reindex(range(7), fill_value=0)
        .round(0)
    )

    # 3 & 4 & 5 & 6. Per-product aggregation (with Categoría for category splits)
    by_product_cat = (
        df.groupby(["Producto", "Categoría"])
        .agg(cantidad=("Cantidad", "sum"), ingreso_sin_iva=("ingreso_sin_iva", "sum"))
        .reset_index()
    )
    by_product_cat["ingreso_sin_iva"] = by_product_cat["ingreso_sin_iva"].round(0)

    # Rolled-up totals (for pie / scatter which don't need category)
    by_product = (
        by_product_cat.groupby("Producto")
        .agg(cantidad=("cantidad", "sum"), ingreso_sin_iva=("ingreso_sin_iva", "sum"))
        .reset_index()
    )

    def _top10(sub, metric):
        return [
            {"Producto": r["Producto"], metric: float(r[metric])}
            for r in sub.nlargest(10, metric)[["Producto", metric]].to_dict(
                orient="records"
            )
        ]

    esp = by_product_cat[by_product_cat["Categoría"] == "Especialidades"]
    ext = by_product_cat[by_product_cat["Categoría"] == "Extras"]

    top10_qty = _top10(by_product, "cantidad")
    top10_rev = _top10(by_product, "ingreso_sin_iva")
    top10_qty_esp = _top10(esp, "cantidad")
    top10_rev_esp = _top10(esp, "ingreso_sin_iva")
    top10_qty_ext = _top10(ext, "cantidad")
    top10_rev_ext = _top10(ext, "ingreso_sin_iva")

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

    # ── Channel split (Uber Eats vs Local) ────────────────────────────────────
    df["_canal"] = df["Creada por"].apply(
        lambda x: "Uber Eats" if str(x).lower() == "uber_eats" else "Local"
    )
    CHANNELS = ["Uber Eats", "Local"]
    ch_units = df.groupby("_canal")["Cantidad"].sum().reindex(CHANNELS, fill_value=0)
    ch_revenue = (
        df.groupby("_canal")["ingreso_sin_iva"]
        .sum()
        .reindex(CHANNELS, fill_value=0)
        .round(0)
    )

    # Category × channel (Especialidades and Extras only)
    CATS = ["Especialidades", "Extras"]
    cat_ch = (
        df[df["Categoría"].isin(CATS)]
        .groupby(["Categoría", "_canal"])
        .agg(cantidad=("Cantidad", "sum"), ingreso_sin_iva=("ingreso_sin_iva", "sum"))
        .reset_index()
    )
    cat_ch["ingreso_sin_iva"] = cat_ch["ingreso_sin_iva"].round(0)

    def _cat_ch_val(cat, ch, col):
        sub = cat_ch[(cat_ch["Categoría"] == cat) & (cat_ch["_canal"] == ch)]
        return float(sub[col].sum()) if not sub.empty else 0.0

    channel_by_category = {
        cat: {
            ch: {
                "units": int(_cat_ch_val(cat, ch, "cantidad")),
                "revenue": float(_cat_ch_val(cat, ch, "ingreso_sin_iva")),
            }
            for ch in CHANNELS
        }
        for cat in CATS
    }

    return {
        "hourly": {
            "labels": list(range(24)),
            "count": [int(v) for v in hourly_count.tolist()],
            "revenue": [float(v) for v in hourly_revenue.tolist()],
        },
        "daily": {
            "labels": active_days,
            "count": [int(daily_count[d]) for d in active_days],
            "revenue": [float(daily_revenue[d]) for d in active_days],
        },
        "weekday": {
            "labels": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
            "count": [int(weekday_count[d]) for d in range(7)],
            "revenue": [float(weekday_revenue[d]) for d in range(7)],
        },
        "top10_quantity": top10_qty,
        "top10_revenue": top10_rev,
        "top10_quantity_especialidades": top10_qty_esp,
        "top10_revenue_especialidades": top10_rev_esp,
        "top10_quantity_extras": top10_qty_ext,
        "top10_revenue_extras": top10_rev_ext,
        "pie_quantity": {"labels": pie_labels, "values": pie_values},
        "scatter": [
            {
                "Producto": r["Producto"],
                "cantidad": float(r["cantidad"]),
                "ingreso_sin_iva": float(r["ingreso_sin_iva"]),
            }
            for r in scatter
        ],
        "channel_split": {
            "labels": CHANNELS,
            "units": [int(ch_units[c]) for c in CHANNELS],
            "revenue": [float(ch_revenue[c]) for c in CHANNELS],
        },
        "channel_by_category": channel_by_category,
    }
