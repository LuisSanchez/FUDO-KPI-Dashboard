import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

def get_sales_table(df: pd.DataFrame, by_channel: bool = True) -> List[Dict]:
    """Aggregate sales by product for table display.

    Parameters
    ----------
    by_channel : bool
        When True (default), splits each product row by channel (Uber Eats / Local).
        When False, aggregates all channels together (used by the PDF report).
    """
    if df.empty:
        return []

    df = df.copy()
    df["canal"] = df["Creada por"].apply(
        lambda x: "Uber Eats" if str(x).lower() == "uber_eats" else "Local"
    )

    group_keys = ["Producto", "Categoría"] + (["canal"] if by_channel else [])
    grouped = (
        df.groupby(group_keys)
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
    if "cost_imputed" in df.columns:
        imp = (
            df.groupby(group_keys)["cost_imputed"]
            .sum()
            .reset_index(name="cost_imputed_rows")
        )
        grouped = grouped.merge(imp, on=group_keys, how="left")
        grouped["cost_imputed_rows"] = grouped["cost_imputed_rows"].fillna(0).astype(int)
    else:
        grouped["cost_imputed_rows"] = 0
    grouped["has_imputed_cost"] = grouped["cost_imputed_rows"] > 0

    # Compute percentages before rounding absolute values
    grouped["cmv_pct"] = (
        (grouped["cmv"] / grouped["ingreso_sin_iva"] * 100).round(1).fillna(0)
    )
    grouped["margen_pct"] = (
        (grouped["margen_sin_iva"] / grouped["ingreso_sin_iva"] * 100)
        .round(1)
        .fillna(0)
    )
    # Commission % (sin IVA basis) so that CMV% + comision_pct + margen_pct = 100%
    comision_sin_iva = grouped["comision"] / 1.19
    grouped["comision_pct"] = (
        (comision_sin_iva / grouped["ingreso_sin_iva"] * 100).round(1).fillna(0)
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
    for col in ["cmv_pct", "margen_pct", "comision_pct"]:
        grouped[col] = grouped[col].replace([np.inf, -np.inf], 0)
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

def get_product_prices_table(df: pd.DataFrame) -> List[Dict]:
    """Compute per-product average pricing and raw margin breakdown."""
    if df.empty:
        return []

    df = df.copy()
    df["costo_ingredientes_per_unit_neto"] = df["costo_ingredientes_sin_iva"] / df[
        "Cantidad"
    ].replace(0, 1)
    df["precio_neto_per_unit"] = df["precio_unitario"] / 1.19

    # Average Uber Eats price per product (from uber_eats rows only)
    uber_avg_precio = (
        df[df["Creada por"] == "uber_eats"]
        .groupby("Producto")["precio_unitario"]
        .mean()
        .round(0)
    )

    grouped = (
        df.groupby(["Producto", "Categoría"])
        .agg(
            cantidad=("Cantidad", "sum"),
            avg_precio=("precio_unitario", "mean"),
            avg_precio_neto=("precio_neto_per_unit", "mean"),
            avg_costo_neto=("costo_ingredientes_per_unit_neto", "mean"),
            tiene_uber_eats=("Creada por", lambda x: bool((x == "uber_eats").any())),
        )
        .reset_index()
    )

    grouped["avg_precio_uber_eats"] = (
        grouped["Producto"].map(uber_avg_precio).fillna(0).round(0)
    )

    grouped["avg_iva"] = grouped["avg_precio"] - grouped["avg_precio_neto"]
    grouped["margen_bruto"] = grouped["avg_precio_neto"] - grouped["avg_costo_neto"]
    grouped["pct_costo"] = (
        (grouped["avg_costo_neto"] / grouped["avg_precio_neto"] * 100)
        .round(1)
        .fillna(0)
        .replace([np.inf, -np.inf], 0)
    )
    grouped["pct_margen_bruto"] = (
        (grouped["margen_bruto"] / grouped["avg_precio_neto"] * 100)
        .round(1)
        .fillna(0)
        .replace([np.inf, -np.inf], 0)
    )

    for col in [
        "avg_precio",
        "avg_precio_neto",
        "avg_iva",
        "avg_costo_neto",
        "margen_bruto",
        "avg_precio_uber_eats",
    ]:
        grouped[col] = grouped[col].round(0)

    grouped = grouped.sort_values("avg_precio_neto", ascending=False)

    return [
        {
            "Producto": row["Producto"],
            "Categoría": row["Categoría"],
            "cantidad": int(row["cantidad"]),
            "avg_precio": float(row["avg_precio"]),
            "avg_iva": float(row["avg_iva"]),
            "avg_precio_neto": float(row["avg_precio_neto"]),
            "avg_costo_neto": float(row["avg_costo_neto"]),
            "pct_costo": float(row["pct_costo"]),
            "margen_bruto": float(row["margen_bruto"]),
            "pct_margen_bruto": float(row["pct_margen_bruto"]),
            "tiene_uber_eats": bool(row["tiene_uber_eats"]),
            "avg_precio_uber_eats": float(row["avg_precio_uber_eats"]),
        }
        for _, row in grouped.iterrows()
    ]
