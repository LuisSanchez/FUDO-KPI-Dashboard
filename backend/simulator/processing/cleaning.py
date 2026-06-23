"""Sales data cleaning, cost imputation, and margin derivations."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from .constants import (
    COST_UNIT_OVERRIDES,
    UBER_COMMISSION_RATE,
    ZERO_MODIFIER_PRODUCTS,
)


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
    (longest product name that is contained in *name* wins).
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
    Fill in zero Costo base for known FUDO edge cases and set cost_imputed flags.

    1. **"Extra" promotions** (Categoría == "Extra", costs all zero):
       Look up the product name in *lookup*.
    2. **"Producto Genérico"** with cost 0: resolve via Comentario column.
    3. **Explicit overrides** from COST_UNIT_OVERRIDES.
    4. **Period-max fallback**: for any remaining zero Costo base (except
       "Arma Tu Pizza"), use the max per-unit cost of the same product in the
       same calendar month when available.
    """
    df = df.copy()
    if "cost_imputed" not in df.columns:
        df["cost_imputed"] = False
    if "cost_impute_reason" not in df.columns:
        df["cost_impute_reason"] = ""

    def _apply(idx, unit_cost: float, reason: str) -> None:
        if unit_cost <= 0:
            return
        qty = df.at[idx, "Cantidad"]
        df.at[idx, "Costo base"] = unit_cost * (qty if qty else 1)
        df.at[idx, "cost_imputed"] = True
        df.at[idx, "cost_impute_reason"] = reason

    # 1. Extra promotions
    mask_extra = (
        (df["Categoría"] == "Extra")
        & (df["Costo base"] == 0)
        & (df["Costo modificadores"] == 0)
    )
    for idx in df[mask_extra].index:
        unit_cost = _lookup_cost(df.at[idx, "Producto"], lookup)
        _apply(idx, unit_cost, "extra_promo_lookup")

    # 2. Producto Genérico — resolve via Comentario
    if "Comentario" in df.columns:
        mask_generic = (df["Producto"] == "Producto Genérico") & (df["Costo base"] == 0)
        for idx in df[mask_generic].index:
            comentario = df.at[idx, "Comentario"]
            unit_cost = _lookup_cost(str(comentario), lookup)
            _apply(idx, unit_cost, "generic_comentario_lookup")

    # 3. Explicit unit-cost overrides (optional config)
    for product, unit_cost in COST_UNIT_OVERRIDES.items():
        mask = (df["Producto"] == product) & (df["Costo base"] == 0)
        for idx in df[mask].index:
            _apply(idx, float(unit_cost), "explicit_override")

    # 4. Period-max fallback for remaining zero costs (any product/period)
    #    Replaces the old hard-coded March-2026 product list.
    if "Creación" in df.columns:
        creation = pd.to_datetime(df["Creación"], errors="coerce")
    else:
        creation = pd.to_datetime(df.get("created_at"), errors="coerce")
    period = creation.dt.to_period("M").astype(str)

    skip_cats = {"Arma Tu Pizza"}
    still_zero = (df["Costo base"] == 0) & (~df["Categoría"].isin(skip_cats))
    for idx in df[still_zero].index:
        prod = df.at[idx, "Producto"]
        per = period.at[idx] if idx in period.index else ""
        same = (
            (df["Producto"] == prod)
            & (period == per)
            & (df["Costo base"] > 0)
            & (df["Cantidad"] > 0)
        )
        valid = df.loc[same]
        if valid.empty:
            # Fall back to any period for the product
            same_any = (df["Producto"] == prod) & (df["Costo base"] > 0) & (
                df["Cantidad"] > 0
            )
            valid = df.loc[same_any]
        if valid.empty:
            continue
        unit_costs = valid["Costo base"] / valid["Cantidad"].replace(0, 1)
        _apply(idx, float(unit_costs.max()), "period_max_unit_cost")

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
        if "Comentario" in df.columns:
            cols.append("Comentario")
        df = df[cols].copy()

    df["cost_imputed"] = False
    df["cost_impute_reason"] = ""

    cost_lookup = _build_cost_lookup(df)
    df = _impute_zero_costs(df, cost_lookup)

    for prod in ZERO_MODIFIER_PRODUCTS:
        df.loc[df["Producto"] == prod, "Costo modificadores"] = 0

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
    df["costo_ingredientes_sin_iva"] = (df["Costo total"] - df["comision"]) / 1.19

    df["margen"] = df["ingreso"] - df["Costo total"]
    df["margen_sin_iva"] = df["ingreso_sin_iva"] - df["costo_sin_iva"]

    if "Creación" in df.columns:
        df["created_at"] = pd.to_datetime(df["Creación"], errors="coerce")
        df.drop(columns=["Creación"], inplace=True)
    elif "created_at" not in df.columns:
        df["created_at"] = pd.NaT

    df.sort_values(by="created_at", inplace=True)
    return df


def get_imputation_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Summarise cost imputation applied during cleaning (for API/UI banners)."""
    if df.empty or "cost_imputed" not in df.columns:
        return {"imputed_rows": 0, "imputed_units": 0, "by_reason": {}, "products": []}

    imputed = df[df["cost_imputed"] == True]  # noqa: E712
    if imputed.empty:
        return {"imputed_rows": 0, "imputed_units": 0, "by_reason": {}, "products": []}

    by_reason: Dict[str, int] = (
        imputed["cost_impute_reason"].fillna("unknown").value_counts().astype(int).to_dict()
    )
    products: List[Dict[str, Any]] = (
        imputed.groupby("Producto")
        .agg(rows=("Producto", "size"), units=("Cantidad", "sum"))
        .reset_index()
        .sort_values("units", ascending=False)
        .head(20)
        .to_dict(orient="records")
    )
    for p in products:
        p["rows"] = int(p["rows"])
        p["units"] = float(p["units"])

    return {
        "imputed_rows": int(len(imputed)),
        "imputed_units": float(imputed["Cantidad"].sum()),
        "by_reason": {str(k): int(v) for k, v in by_reason.items()},
        "products": products,
    }
