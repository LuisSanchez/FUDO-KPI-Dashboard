---
name: Project Context
description: Why this project exists and where it's headed
type: project
---

OMP is a personal business tool for a pizza franchise owner to analyze sales vs expenses, track EBITDA and KPIs, and understand costs. Started as Jupyter notebooks, now evolving into a Django + React web app so it can be used by the owner and other franchise members.

**Why:** The engineer wants to provide actionable business insights to non-technical franchise members.

**No persistence yet by design:** SQLite DB exists in backend/ but is intentionally unused for now. Will add a proper DB once the app is tuned. Do not suggest adding persistence.

**Data source:** Excel exports from FUDO software (POS system). All data is in Spanish. Sales file uses "Adiciones" sheet; expenses file uses "Gastos" sheet.

**How to apply:** Prioritize business usefulness and insight quality. The user makes all infra/architecture decisions — don't suggest infrastructure changes unless asked.
