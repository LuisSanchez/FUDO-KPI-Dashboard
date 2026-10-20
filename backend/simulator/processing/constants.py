"""Shared business constants."""

# Legacy model used by the live KPI card and margin charts: 25% of the FUDO
# menu price (Precio), before discounts. IVA on that fee is treated as a credit.
UBER_COMMISSION_RATE = 0.25

# Cash commission measured on Uber settlements: 26% of what the customer paid
# (menu price minus discounts, both IVA-included), before the 19% VAT Uber adds
# on the fee. September 2026 orders and the May Portier invoice land on 26%.
# The withheld "tasa de servicio" is this rate × 1.19. Ads and financing are
# not included — they are not in the FUDO file.
UBER_COLLECTED_COMMISSION_RATE = 0.26

# Payment to people when a month has no remuneraciones line (September is
# empty; June is only trial payments). It replaces that payment, it is not
# added on top, and it does not include Previred. Previred stays in the
# expenses when the file has it. Months with a real remuneraciones line start
# from that file amount instead.
DEFAULT_MONTH_SUELDOS = 1_300_000
