import math
import numpy as np
import pandas as pd
import io
from typing import Dict, Any, List, Optional

# Uber Eats commission: 25% + IVA (19%) — IVA is a recoverable input credit for the
# restaurant, so the net effective rate on the gross sale price is 25%.
UBER_COMMISSION_RATE = 0.25


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
    df.loc[df["Creada por"] == "uber_eats", "comision"] = (
        df["ingreso"] * UBER_COMMISSION_RATE
    )

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

    # ── Dashboard summary KPIs ────────────────────────────────────────────────
    _WEEKDAY_ES = [
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo",
    ]

    # Average price per unit for Especialidades (pizza-like main products)
    esp_df = df[df["Categoría"] == "Especialidades"]
    esp_units = esp_df["Cantidad"].sum()
    avg_precio_especialidades = (
        float(esp_df["ingreso_sin_iva"].sum() / esp_units) if esp_units > 0 else 0.0
    )

    # Gross margin by channel (ingredients + commission vs revenue, all sin IVA)
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

    # Best weekday by total units sold (accumulated across all dates in period)
    wday_units = df.groupby(df["created_at"].dt.dayofweek)["Cantidad"].sum()
    if not wday_units.empty:
        best_wday_idx = int(wday_units.idxmax())
        best_weekday = {
            "label": _WEEKDAY_ES[best_wday_idx],
            "count": int(wday_units.max()),
        }
    else:
        best_weekday = None

    # Best hour by total units sold
    hour_units = df.groupby(df["created_at"].dt.hour)["Cantidad"].sum()
    if not hour_units.empty:
        best_hour_val = int(hour_units.idxmax())
        best_hour = {
            "label": f"{best_hour_val:02d}:00",
            "count": int(hour_units.max()),
        }
    else:
        best_hour = None

    # Top Especialidad by units sold
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


def get_promotion_advisor(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyse current sales data and return promotion recommendations:
    - Top 5 products per category (Especialidades, Extras) ranked by a
      composite score of margin %, low CMV, and volume.
    - Uber Eats hourly activity to suggest best promo windows.
    - Per-order average ticket comparison: Uber Eats vs. local.
    """
    if df.empty:
        return {}

    rows = get_sales_table(df)

    # ── Product scoring ───────────────────────────────────────────────────────
    def _score_products(cat_rows: list) -> list:
        if not cat_rows:
            return []
        max_qty = max(r["cantidad"] for r in cat_rows) or 1
        scored = []
        for r in cat_rows:
            if r["cmv_pct"] <= 0 or r["cantidad"] < 3:
                continue
            volume_score = min(r["cantidad"] / max_qty, 1.0) * 100
            score = (
                r["margen_pct"] * 0.5 + (100 - r["cmv_pct"]) * 0.3 + volume_score * 0.2
            )
            razones = []
            if r["margen_pct"] >= 70:
                razones.append("Margen excelente")
            elif r["margen_pct"] >= 55:
                razones.append("Buen margen")
            if r["cmv_pct"] <= 20:
                razones.append("Costo muy bajo")
            elif r["cmv_pct"] <= 30:
                razones.append("Costo bajo")
            if r["cantidad"] >= max_qty * 0.6:
                razones.append("Alta rotación")
            elif r["cantidad"] >= max_qty * 0.3:
                razones.append("Buena rotación")
            if r["comision_pct"] > 0:
                razones.append(f"Ya en Uber Eats ({r['comision_pct']}% comisión)")
            scored.append({**r, "score": round(score, 1), "razones": razones[:3]})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:5]

    esp_rows = [r for r in rows if r["Categoría"] == "Especialidades"]
    ext_rows = [r for r in rows if r["Categoría"] == "Extras"]

    # ── Uber Eats hourly pattern ───────────────────────────────────────────────
    df_ue = df[df["Creada por"] == "uber_eats"].copy()
    df_lo = df[df["Creada por"] != "uber_eats"].copy()

    ue_hourly: Dict[int, Dict] = {}
    if not df_ue.empty:
        df_ue["hour"] = df_ue["created_at"].dt.hour
        hg = (
            df_ue.groupby("hour")
            .agg(count=("Cantidad", "sum"), revenue=("ingreso_sin_iva", "sum"))
            .reindex(range(24), fill_value=0)
        )
        ue_hourly = {
            h: {
                "count": int(hg.loc[h, "count"]),
                "revenue": float(round(hg.loc[h, "revenue"], 0)),
            }
            for h in range(24)
        }

    peak_count = max((v["count"] for v in ue_hourly.values()), default=0)
    best_hours = sorted(
        [
            h
            for h, v in ue_hourly.items()
            if v["count"] >= peak_count * 0.6 and v["count"] > 0
        ],
        key=lambda h: ue_hourly[h]["count"],
        reverse=True,
    )[:4]
    slow_hours = sorted(
        [h for h, v in ue_hourly.items() if 0 < v["count"] < peak_count * 0.5],
        key=lambda h: ue_hourly[h]["count"],
        reverse=True,
    )[:3]

    # ── Best weekday for Uber Eats ─────────────────────────────────────────────
    WEEKDAY_NAMES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    best_ue_day = ""
    if not df_ue.empty:
        wd = df_ue.groupby(df_ue["created_at"].dt.dayofweek)["Cantidad"].sum()
        best_ue_day = WEEKDAY_NAMES[int(wd.idxmax())] if not wd.empty else ""

    # ── Average ticket per order (group line items by Id. Venta) ──────────────
    def _avg_ticket(sub: pd.DataFrame) -> float:
        if sub.empty or "Id. Venta" not in sub.columns:
            return 0.0
        per_order = sub.groupby("Id. Venta")["ingreso_sin_iva"].sum()
        return float(round(per_order.mean(), 0)) if not per_order.empty else 0.0

    avg_ticket_uber = _avg_ticket(df_ue)
    avg_ticket_local = _avg_ticket(df_lo)
    ue_units = int(df_ue["Cantidad"].sum()) if not df_ue.empty else 0
    total_units = int(df["Cantidad"].sum()) if not df.empty else 1
    ue_pct = round(ue_units / total_units * 100, 1) if total_units > 0 else 0.0

    return {
        "especialidades": _score_products(esp_rows),
        "extras": _score_products(ext_rows),
        "uber_hours": ue_hourly,
        "best_hours": best_hours,
        "slow_hours": slow_hours,
        "best_weekday": best_ue_day,
        "avg_ticket_uber": avg_ticket_uber,
        "avg_ticket_local": avg_ticket_local,
        "uber_pct_of_units": ue_pct,
        "uber_units": ue_units,
    }


def get_sales_excel(df: pd.DataFrame, categoria: str) -> bytes:
    """
    Build an Excel workbook for a single category (e.g. 'Especialidades' or 'Extras')
    containing all products with full calculated columns.  Returns raw bytes.
    """
    import io

    rows = [
        r
        for r in get_sales_table(df, by_channel=True)
        if r.get("Categoría") == categoria
    ]

    col_map = {
        "Producto": "Producto",
        "canal": "Canal",
        "cantidad": "Cantidad",
        "ingreso_sin_iva": "Ingreso s/IVA",
        "cmv": "CMV ($)",
        "cmv_pct": "CMV (%)",
        "comision": "Comisión ($)",
        "comision_pct": "Comisión (%)",
        "margen_sin_iva": "Margen ($)",
        "margen_pct": "Margen (%)",
    }

    export_df = pd.DataFrame([{col_map[k]: r[k] for k in col_map} for r in rows])

    buf = io.BytesIO()
    export_df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


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


# ── Sunday viability analysis ──────────────────────────────────────────────────

_SUNDAY_BUCKETS: dict[str, list[str]] = {
    "Arriendo": ["arriendo"],
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
