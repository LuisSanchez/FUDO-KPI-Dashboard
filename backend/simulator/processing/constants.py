"""Shared constants for pizza finance analytics."""

# Uber Eats commission: 25% + IVA (19%) — IVA is a recoverable input credit for the
# restaurant, so the net effective rate on the gross sale price is 25%.
UBER_COMMISSION_RATE = 0.25

# Products whose modifier cost is embedded in the parent combo line and must be zeroed.
ZERO_MODIFIER_PRODUCTS = (
    "Duo Familiar (2pizzas)",
    "Lunes de Duo 2x1",
)

# Optional explicit unit-cost overrides: {product_name: unit_cost_clp_gross}.
# Prefer automatic period-max imputation; use this only for known FUDO export gaps.
COST_UNIT_OVERRIDES: dict[str, float] = {}
