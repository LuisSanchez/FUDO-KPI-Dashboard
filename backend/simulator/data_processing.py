import math
import numpy as np
import pandas as pd
import io
from typing import Dict, Any, List, Optional


def _build_cost_lookup(df: pd.DataFrame) -> Dict[str, float]:
    """
    Build a {product_name: avg_costo_base_per_unit} dict from rows that have
    a valid (non-zero) Costo base and belong to a normal sales category.
    Rows in "Extra" / "Arma Tu Pizza" categories and "Producto Genérico" are
    excluded so they don't pollute the reference costs.
    """
    exclude_cats = {"Extra", "Arma Tu Pizza"}
    valid = df[
        (df["Costo base"] > 0)
        & (~df["Categoría"].isin(exclude_cats))
        & (df["Producto"] != "Producto Genérico")
    ].copy()

    if valid.empty:
        return {}

    valid["_unit_cost"] = valid["Costo base"] / valid["Cantidad"].replace(0, 1)
    return valid.groupby("Producto")["_unit_cost"].mean().to_dict()


def _lookup_cost(name: str, lookup: Dict[str, float]) -> float:
    """
    Return the per-unit Costo base for *name* from the lookup table.
    Tries exact match first, then case-insensitive, then substring containment
    (longest product name that is contained in *name* wins, to handle cases
    where Comentario has extra text around the product name).
    Returns 0.0 if nothing matches.
    """
    if not name or pd.isna(name):
        return 0.0
    name = str(name).strip()

    if name in lookup:
        return lookup[name]

    name_lower = name.lower()
    for key, val in lookup.items():
        if key.lower() == name_lower:
            return val

    # Substring: pick the longest key that fits inside name (or name inside key)
    best_val, best_len = 0.0, 0
    for key, val in lookup.items():
        k = key.lower()
        if k in name_lower and len(k) > best_len:
            best_val, best_len = val, len(k)
        elif name_lower in k and len(name_lower) > best_len:
            best_val, best_len = val, len(name_lower)

    return best_val


def _impute_zero_costs(df: pd.DataFrame, lookup: Dict[str, float]) -> pd.DataFrame:
    """
    Fill in zero Costo base for two known edge cases:

    1. **"Extra" promotions** (Categoría == "Extra", Costo base == 0, Costo modificadores == 0):
       The product is included as a promotion so its price is 0, but the ingredient
       cost is real. Look up the product name in *lookup* and assign
       Costo base = unit_cost × Cantidad.

    2. **"Producto Genérico"** (Producto == "Producto Genérico", Costo base == 0):
       FUDO records these with a placeholder name. The real product name lives in
       the "Comentario" column. Look up that name in *lookup*.

    "Arma Tu Pizza" category items intentionally have Costo base == 0 (their cost
    is embedded in the parent pizza) and are NOT modified here.
    """
    df = df.copy()

    # 1. Extra promotions
    mask_extra = (
        (df["Categoría"] == "Extra")
        & (df["Costo base"] == 0)
        & (df["Costo modificadores"] == 0)
    )
    for idx in df[mask_extra].index:
        unit_cost = _lookup_cost(df.at[idx, "Producto"], lookup)
        if unit_cost > 0:
            df.at[idx, "Costo base"] = unit_cost * df.at[idx, "Cantidad"]

    # 2. Producto Genérico — resolve via Comentario
    if "Comentario" in df.columns:
        mask_generic = (df["Producto"] == "Producto Genérico") & (df["Costo base"] == 0)
        for idx in df[mask_generic].index:
            comentario = df.at[idx, "Comentario"]
            unit_cost = _lookup_cost(str(comentario), lookup)
            if unit_cost > 0:
                df.at[idx, "Costo base"] = unit_cost * df.at[idx, "Cantidad"]

    return df


def sales_clean_up_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean up sales dataframe and calculate margins."""
    if "Creación" in df.columns:
        cols = [
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
        # Keep Comentario when present — needed to resolve "Producto Genérico" costs
        if "Comentario" in df.columns:
            cols.append("Comentario")
        df = df[cols].copy()

    # Build reference cost table, then impute missing costs before any derivations
    cost_lookup = _build_cost_lookup(df)
    df = _impute_zero_costs(df, cost_lookup)

    # ── Patch: FUDO did not backfill costs for these products in March 2026.
    # At least one sale row has the correct cost; use the highest per-unit value found.
    _PATCH_PRODUCTS = ["Pizza Napoli", "Pizza Veggie G"]
    _PATCH_PERIOD = "2026-03"
    _creation_period = (
        pd.to_datetime(df["Creación"], errors="coerce").dt.to_period("M").astype(str)
    )
    for _prod in _PATCH_PRODUCTS:
        _in_period = (_creation_period == _PATCH_PERIOD) & (df["Producto"] == _prod)
        _valid = df[_in_period & (df["Costo base"] > 0)]
        if not _valid.empty:
            _best_unit_cost = (
                _valid["Costo base"] / _valid["Cantidad"].replace(0, 1)
            ).max()
            _zero_mask = _in_period & (df["Costo base"] == 0)
            df.loc[_zero_mask, "Costo base"] = (
                _best_unit_cost * df.loc[_zero_mask, "Cantidad"]
            )

    # if Producto column is 'Duo Familiar (2pizzas)' set Costo modificadores to 0
    df.loc[df["Producto"] == "Duo Familiar (2pizzas)", "Costo modificadores"] = 0
    df.loc[df["Producto"] == "Lunes de Duo 2x1", "Costo modificadores"] = 0

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

    # EBITDA = revenue − all operational expenses.
    # We do NOT subtract FUDO COGS here because gastos_totales already includes
    # the actual ingredient purchases (Materia Prima) from the expenses file.
    # Subtracting total_margen_sin_iva (which already deducts FUDO COGS) would
    # double-count ingredient costs. The gross margin is shown separately in the
    # UI for per-product analysis only.
    ebitda = total_ingreso_sin_iva - gastos_totales - sueldos
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
            avg_costo_ing_per_unit = (
                product_df["costo_ingredientes_sin_iva"] / quantities
            ).mean()
            # Contribution per unit = ingreso − ingredient cost only.
            # Uber Eats commission is NOT in the expense file (Uber pays net),
            # so it is not a variable cost in the EBITDA = ingreso − gastos model.
            avg_contribution_per_unit = avg_ingreso_per_unit - avg_costo_ing_per_unit
            margen_pct = (
                float(round(avg_margen_per_unit / avg_ingreso_per_unit * 100, 1))
                if avg_ingreso_per_unit > 0
                else 0
            )

            already_breakeven = ebitda >= 0
            already_25pct = ebitda_percentage >= 25

            # Breakeven: ebitda + x*c = 0  →  x = -ebitda / c
            # where c = avg_contribution_per_unit (ingreso − ingredient COGS)
            if already_breakeven:
                breakeven_units = 0
            elif avg_contribution_per_unit > 0:
                breakeven_units = math.ceil(-ebitda / avg_contribution_per_unit)
            else:
                breakeven_units = None  # contribution negative, can't break even

            # 25% EBITDA: (ebitda + x*c) / (I + x*i) = 0.25
            # x = (0.25*I - ebitda) / (c - 0.25*i)
            if already_25pct:
                target_25_units = 0
            else:
                denom = avg_contribution_per_unit - 0.25 * avg_ingreso_per_unit
                if denom > 0:
                    numer = 0.25 * total_ingreso_sin_iva - ebitda
                    target_25_units = max(0, math.ceil(numer / denom))
                else:
                    target_25_units = (
                        None  # product margin % too low to ever reach 25% EBITDA
                    )

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
    }


def get_product_prices_table(df: pd.DataFrame) -> List[Dict]:
    """Compute per-product average pricing and raw margin breakdown."""
    if df.empty:
        return []

    df = df.copy()
    df["costo_ingredientes_per_unit_neto"] = df["costo_ingredientes_sin_iva"] / df[
        "Cantidad"
    ].replace(0, 1)
    df["precio_neto_per_unit"] = df["precio_unitario"] / 1.19

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
        }
        for _, row in grouped.iterrows()
    ]


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

    def r(v):
        return float(round(v, 0))

    return {
        "units_sold": int(total_units),
        "esp_units_sold": int(esp_units),
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
        "cmv_sin_iva_projected": r(total_costo_ing_sin_iva + cost_delta),
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
