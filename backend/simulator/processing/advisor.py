from typing import Dict, Any

import pandas as pd

from .tables import get_sales_table

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
