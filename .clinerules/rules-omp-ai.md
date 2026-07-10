# OMP / FUDO Analytics — agent rules (Cline)

Canonical context: **AGENTS.md** at repo root. Claude index: **CLAUDE.md**.

## Must follow

- Read `AGENTS.md` before non-trivial changes.
- Put business logic in `backend/simulator/processing/engine.py`; keep views thin.
- Unit tests required for logic/API/hook changes; coverage gates ≥75% (pre-commit / CI).
- Notebooks (`backend/lab/`): **create new cells**; do not delete existing cells unless asked. Prefer **Plotly**.
- Do not set `axios.defaults.baseURL` in frontend dev (breaks session cookies via proxy).
- Do not make Neon/OAuth mandatory without an explicit request.
