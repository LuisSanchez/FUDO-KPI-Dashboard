# Bug Review Log

---

## BUG-001 — Uber Eats promotion items exported with zero ingredient cost

**Severity**: Medium (affects EBITDA accuracy — understates real COGS)
**Status**: Mitigated in code (cost imputation applied at import time)
**Affected file**: `backend/simulator/data_processing.py` → `_impute_zero_costs()`

---

### Description

When an order is placed through Uber Eats and includes a promotional item (e.g. a free pizza bundled with a combo), FUDO records the line item with:

- `Categoría` = `"Extra"`
- `Precio` = `0` (expected — promotion price)
- `Costo base` = `0` ← **incorrect**
- `Costo modificadores` = `0`
- `Creada por` = `"uber_eats"`

The same promotion type created through FUDO's own POS (non-Uber Eats orders) records the correct `Costo base`. The zero cost is therefore **not** a business decision — it is a data export defect in the FUDO ↔ Uber Eats integration.

**Impact**: Without mitigation, all Uber Eats promotion items have `costo_ingredientes_sin_iva = 0`, understating total CMV and overstating EBITDA.

---

### Example case — Id. Venta 1861
Uber ID 
https://merchants.ubereats.com/manager/orders/5a5e0548-b823-4d40-9b7e-884b8d4c6b40

| Field               | Value                     |
|---------------------|---------------------------|
| Id. Venta           | 1861                      |
| Creada por          | `uber_eats`               |
| Categoría           | `Extra`                   |
| Producto            | (promoted pizza name)     |
| Cantidad            | 1                         |
| Precio              | 0                         |
| Costo base          | **0** ← wrong             |
| Costo modificadores | 0                         |
| Expected cost       | unit cost × Cantidad (from lookup built off normal sales rows) |

On the same Id. Venta 1861 there are also rows with `Categoría = "Arma Tu Pizza"` — those legitimately have zero cost (their ingredient cost is embedded in the parent pizza line) and must **not** be imputed.

---

### Root cause hypothesis

FUDO likely sends a simplified payload to the Uber Eats integration layer that omits `Costo base` for add-on / promotion rows. The integration records the field as `0` instead of `null`, making it indistinguishable from a truly free item at the database level. This is an upstream data quality issue outside our control.

---

### Mitigation applied (2026-03-29)

`_impute_zero_costs()` in `data_processing.py` corrects the value at import time:

```python
mask_extra = (
    (df["Categoría"] == "Extra")
    & (df["Costo base"] == 0)
    & (df["Costo modificadores"] == 0)
)
for idx in df[mask_extra].index:
    unit_cost = _lookup_cost(df.at[idx, "Producto"], lookup)
    if unit_cost > 0:
        df.at[idx, "Costo base"] = unit_cost * df.at[idx, "Cantidad"]
```

The lookup is built from all non-Extra, non-Arma-Tu-Pizza, non-Producto-Genérico rows where `Costo base > 0`. Match strategy: exact name → case-insensitive exact → longest substring.

**Known limitation**: The current mask applies to ALL `"Extra"` rows with zero cost, not just Uber Eats ones. This is intentionally broad — if a non-Uber-Eats Extra row somehow also has zero cost it will also be corrected, which is the desired behavior. If a distinction is ever needed, add `& (df["Creada por"] == "uber_eats")` to the mask.

---

### Future review checklist

- [ ] Confirm with FUDO support whether the `Costo base = 0` on Uber Eats Extra rows is a known bug or intended behavior.
- [ ] Check whether new FUDO exports still exhibit this pattern after any FUDO version upgrades.
- [ ] If FUDO fixes the root cause, remove or gate the `mask_extra` imputation to avoid double-correction.
- [ ] Validate that no legitimate zero-cost promotion items (intentionally free, zero ingredients) are being incorrectly assigned a cost by this imputation.
- [ ] Cross-check Id. Venta 1861 in a corrected export once FUDO fix is available, to validate the lookup match produces the expected unit cost.
