import io

import pandas as pd

from .tables import get_sales_table

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
