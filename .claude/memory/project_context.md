---
name: Project Context
description: Why this project exists and where it's headed
type: project
---

OMP is a personal business tool for a pizza franchise owner to analyze sales vs expenses, track EBITDA and KPIs, and understand costs. Started as Jupyter notebooks, now evolving into a Django + React web app so it can be used by the owner and other franchise members.

**Why:** The engineer wants to provide actionable business insights to non-technical franchise members.

**Session-based storage:** SQLite is used only for short-lived `UserSessionData` (pickled DataFrames, 24h expiry). No persistent user accounts or business data by design — each upload is a fresh session. Do not suggest adding user persistence unless asked.

**Data source:** Excel exports from FUDO software (POS system). All data is in Spanish. Sales file uses "Adiciones" sheet; expenses file uses "Gastos" sheet.

**How to apply:** Prioritize business usefulness and insight quality. The user makes all infra/architecture decisions — don't suggest infrastructure changes unless asked.
