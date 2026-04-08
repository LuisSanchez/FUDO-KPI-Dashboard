# Updated AI Instructions: Price Verification – Uber Eats vs In-Store (Counter)

## 1. Objective

Verify that the pricing logic between **in-store sales** (from your POS/backend) and **Uber Eats sales** (marked by `creada por = "uber_eats"`) is mathematically consistent, tax-compliant (Chilean IVA 19%), and profitable. The AI will use actual sales data from your exported file.

---

## 2. Input Data Schema (from your Excel/CSV)

The AI will receive a table with the following columns. **All monetary values are in CLP and include IVA (19%), including costs (`Costo base`, `Costo modificadores`, `Costo total`).**

| Column Name | Type | Description | Example |
|-------------|------|-------------|---------|
| `Id. Venta` | integer | Sale ID (can group multiple rows per sale) | 1988 |
| `Creación` | datetime | Timestamp of the order | 2026-04-07 20:48:19 |
| `Producto` | string | Name of the product | "Pizza Pepperoni" |
| `Categoría` | string | Product category (see §2.1) | "Especialidades", "Extras", "Combo" |
| `Cantidad` | integer | Quantity sold | 1 |
| `Precio` | float | Unit price **including IVA** paid by customer | 8990 |
| `Costo base` | float | Base cost of goods (without modifiers) | 1862.02 |
| `Costo modificadores` | float | Additional cost for modifiers/toppings | 0 |
| `Costo total` | float | Sum of `Costo base + Costo modificadores` | 1862.02 |
| `Creada por` | string | Source of order: `"caja1"`, `"admin"` (in-store), or `"uber_eats"` | "caja1", "uber_eats" |
| `Cocina` | string | Kitchen status (ignore for pricing) | "Cocina" |
| `Cancelada` | string | "Si" if cancelled, "No" otherwise | "No" |

### 2.1 Important Category Mapping

The AI must recognize these categories for proper validation:

| Category | Type | Notes |
|----------|------|-------|
| `Especialidades` | Pizza (main product) | Core product, high margin |
| `Extras` | Side items | Alitas, papas, empanaditas, palitos, etc. |
| `Combo` | Bundle | Multiple items sold together |
| `Promociones` | Promotional / discounted | Price may already be reduced |
| `Bebida Andina`, `Bebidas` | Drinks | Low margin, high volume |
| `Postres` | Dessert | e.g., Palitos de Canela |
| `Arma Tu Pizza` | Build-your-own components | Usually zero-cost base (mozzarella, salsa) – these are **components**, not sellable products. They should be **grouped** with the parent pizza (same `Id. Venta`). |
| `Cup de salsas` | Sauce cups | Often zero-price add-ons |

### 2.2 Special Handling for Zero-Cost Rows

Rows where `Costo total = 0` and `Precio = 0` (e.g., "Base Queso Mozzarella", "Base Salsa de Tomate", "Cup de BBQ") are **product components**, not independent sales. The AI must:

- **Ignore them** for margin calculations on individual products.
- **Group them** under the same `Id. Venta` with the main product that has a positive `Precio` (typically the pizza in `Especialidades` or `Combo`). The cost is already accounted in the parent product's `Costo total`.

---

## 3. Data Preprocessing Instructions (for the AI)

Before running formulas, the AI must:

1. **Filter out cancelled orders**: `Cancelada = "Si"` → exclude.
2. **Separate in-store vs Uber Eats**:
   - In-store: `Creada por` IN (`"caja1"`, `"admin"`) → treat as counter sale.
   - Uber Eats: `Creada por = "uber_eats"` → treat as delivery sale.
3. **Group components** (zero-cost, zero-price rows) with their parent product using `Id. Venta`. The parent is the row with `Precio > 0` in the same sale. For combos, the `Precio` is already the combo price; the `Costo total` of the combo row includes all items.
4. **Extract unique products** by `Producto` name (case-sensitive). If the same product appears with different prices (e.g., promo vs regular), treat as separate variants (e.g., "Oh My Luco" vs "Oh My Luco (Lunes a Jueves)").

---

## 4. Input Fields for Price Verification (per product)

For each unique product (or product variant), the AI will need:

| Field | Source Column | Description |
|-------|---------------|-------------|
| `product_name` | `Producto` | Exact name as in the file |
| `category` | `Categoría` | For classification |
| `in_store_price` | `Precio` where `Creada por` is `"caja1"` or `"admin"` | Most frequent or average in-store price (including IVA) |
| `uber_eats_price` | `Precio` where `Creada por` is `"uber_eats"` | Current Uber Eats price (including IVA) |
| `costo_producto` | `Costo total` for that product | Cost of goods sold (materia prima) – **includes IVA** (FUDO reports costs con IVA; divide by 1.19 for net cost) |
| `uber_eats_commission_rate` | User-provided or default | 0.25 (25%) for delivery, 0.20 (20%) for pickup |
| `iva_rate` | Fixed | 0.19 (19%) |

If a product appears only in-store or only on Uber Eats, the missing price must be **inferred** or requested from the user.

---

## 5. Core Formulas (unchanged from previous instructions)

Use the same formulas as defined earlier:

### 5.1 IVA Extraction
```
precio_sin_iva = precio_con_iva / (1 + iva_rate)
iva_amount = precio_con_iva - precio_sin_iva
```

### 5.2 In-Store Net Margin
```
ingreso_sin_iva      = in_store_price / 1.19
costo_sin_iva        = costo_producto / 1.19        # FUDO costs include IVA
in_store_margin      = ingreso_sin_iva - costo_sin_iva
in_store_margin_pct  = (in_store_margin / ingreso_sin_iva) * 100
```

### 5.3 Uber Eats Net Revenue (Delivery)

Uber charges 25% on the net order value. The commission factura includes IVA, but that IVA is a recoverable input credit for the restaurant. The net cost is 25% of net revenue.

```
ingreso_sin_iva   = uber_eats_price / 1.19
comision_gross    = uber_eats_price * 0.25           # total deducted by Uber (= neto commission * 1.19)
comision_sin_iva  = comision_gross / 1.19            # net cost (IVA on commission is recoverable)
costo_sin_iva     = costo_producto / 1.19            # FUDO costs include IVA
uber_margin       = ingreso_sin_iva - costo_sin_iva - comision_sin_iva
uber_margin_pct   = (uber_margin / ingreso_sin_iva) * 100
```

> **Correction:** The previous formula `combined_commission_factor = 0.25 * 1.19 = 0.2975` was incorrect.
> It conflated IVA extraction and commission deduction into one step, producing a number that is
> neither revenue sin IVA nor cash received. The correct approach is to compute everything sin IVA
> separately, as shown above.

### 5.4 Break-Even Price to Match In-Store Margin

To find the Uber Eats price (con IVA) that yields the same margin as in-store:

```
target_margin     = in_store_margin                  # already sin IVA
```
Since `comision_sin_iva = P / 1.19 * 0.25`, net revenue after commission is `P / 1.19 * 0.75`:
```
P / 1.19 * 0.75   = target_margin + costo_sin_iva
P                  = (target_margin + costo_sin_iva) * 1.19 / 0.75
```

---

## 6. Special Validation Rules for Your Data

Based on the file, the AI must also check:

| Rule | Condition | Flag |
|------|-----------|------|
| **Zero-cost combos** | `Categoría = "Combo"` and `Costo total = 0` → likely missing data. Flag for user review. | "WARNING: Combo has zero cost. Verify." |
| **Promo price mismatch** | Same product has lower price in `Promociones` category vs `Especialidades`. Flag for consistency check. | "INFO: Promotional price differs from regular. Verify if intentional." |
| **Uber Eats price lower than in-store** | `uber_eats_price < in_store_price` | "WARNING: Uber price is lower than in-store. Margin erosion likely." |
| **Missing cost for a product** | `costo_producto = 0` for a non-component product (e.g., "Oh My Luco" with `Costo total 0` but positive price). | "ERROR: Missing cost data for product." |
| **Duplicate product names** | Same `Producto` appears with different `Costo total` values. | "INFO: Inconsistent cost. Use most frequent or ask user." |

---

## 7. Output Format (JSON example)

For each verified product, the AI should return:

```json
{
  "product_name": "Pizza Pepperoni",
  "category": "Especialidades",
  "in_store": {
    "price_con_iva": 8990,
    "ingreso_sin_iva": 7555,
    "iva_amount": 1435,
    "costo_con_iva": 1862.02,
    "costo_sin_iva": 1564.72,
    "margin_sin_iva": 5990.28,
    "margin_pct": 79.3
  },
  "uber_eats": {
    "price_con_iva": 12488,
    "ingreso_sin_iva": 10494.12,
    "commission_rate": 0.25,
    "comision_sin_iva": 2623.53,
    "costo_sin_iva": 1564.72,
    "margin_sin_iva": 6305.87,
    "margin_pct": 60.1
  },
  "comparison": {
    "margin_difference_sin_iva": 315.59,
    "margin_pct_difference": -19.2,
    "uber_price_vs_in_store": "+3498 CLP (+38.9%)",
    "is_profitable": true
  },
  "recommendations": [
    "Uber price is 39% higher than in-store, compensating for 25% commission.",
    "Uber margin 60.1% vs in-store 79.3%: lower % but still profitable.",
    "Break-even Uber price (to match in-store margin): (5990 + 1565) * 1.19 / 0.75 = $11,982 CLP."
  ],
  "flags": []
}
```

---

## 8. Integration Notes for Your Python Backend

Your backend should provide a function that reads the Excel/CSV and returns a normalized product list:

```python
def get_product_prices_from_sales(file_path):
    """
    Reads the sales file and returns a dict with product_name as key,
    containing in_store_price, uber_eats_price, and costo_total.
    """
    # Implementation: group by Producto, filter Cancellada != "Si",
    # separate by Creada por, compute average price for each source.
    # Skip rows with Precio == 0 and Costo total == 0 (components).
    pass
```

The AI will then call this logic conceptually.

---

## 9. Example User Query & Expected AI Response (using your file)

**User:** *"Verify my pizza pepperoni using the attached sales data."*

**AI Response (based on file):**

```
VERIFICATION REPORT – Pizza Pepperoni (all values sin IVA)

📊 Data extracted from sales:
- In-store price: $8,990 con IVA → $7,555 sin IVA
- Uber Eats price: $12,488 con IVA → $10,494 sin IVA
- Costo FUDO: $1,862 con IVA → $1,565 sin IVA

✅ In-store margin: $5,990 (79.3% s/IVA)
✅ Uber margin: $6,306 (60.1% s/IVA) – profitable despite 25% commission

🔍 Analysis:
Uber Eats price is 39% above in-store price. After deducting commission ($2,624 s/IVA)
and ingredients ($1,565 s/IVA), net margin is $6,306 per pizza.
Margin % is lower (60% vs 79%) due to commission, but absolute margin is higher.

💡 Recommendation:
- Break-even Uber price to match in-store margin%: $11,982 con IVA
- If you want volume, lower to $9,990 → margin $4,225 (still 50.5% s/IVA)
- Current pricing is profitable — no action required.
```

---
