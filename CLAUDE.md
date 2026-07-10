# CLAUDE.md

Guidance for Claude Code (and compatible agents) in this repository.

**Canonical architecture & commands:** see [`AGENTS.md`](AGENTS.md) first — keep that file accurate when the system changes. This file is a short Claude-oriented index; do not fork long architecture prose here.

## Overview

**OMP / FUDO Analytics** — pizza franchise EBITDA simulator. Django REST API + React SPA. FUDO Excel uploads → session-scoped KPIs, charts, Uber Eats / Sunday analysis, PDF & Excel exports.

## Commands

```bash
make dev          # Runtime deps (backend + frontend)
make dev-tools    # Dev deps + pre-commit install
make run          # Django :8000 + React :3000
make check        # lint + unit tests (coverage ≥75%)
make test-be      # backend pytest + coverage
make test-fe      # frontend Jest + coverage
make lint         # ruff + eslint
make migrate      # Django migrate
make lab          # Jupyter (append cells only; Plotly)
```

Docker: `make build` / `make up` / `make down` (production image). Compose live-reload when using project compose file.

Details, API table, and module map → **AGENTS.md**.

## Architecture (one paragraph)

- **Views** (`simulator/views.py`, `auth_views.py`) — thin HTTP.
- **Session store** (`services/session_store.py`) — pickle DataFrames on `UserSessionData`.
- **Business logic** — `processing/engine.py` (+ `constants.py`). Import via facade `data_processing.py` (stable public path).
- **PDF** — `report.py`.
- **Frontend** — `App.js` shell; `api/client.js`; hooks (`useSimulatorData`, `useAuth`, downloads); charts under `charts/`; components under `components/`. Proxy `/api` via `setupProxy.js` — never set `axios.defaults.baseURL` in dev.

Optional Neon + Google OAuth: [`docs/AUTH_AND_NEON.md`](docs/AUTH_AND_NEON.md) (defaults off).

## Critical business invariants

Do not regress these without an explicit product decision:

1. EBITDA = net revenue − **operational** expenses only (no double-count of FUDO COGS; exclude loans/CapEx).
2. Net of **19% IVA**; Uber commission effective **25%** on gross for Uber rows.
3. Break-even / targets in **tickets** (`Id. Venta`) where the product already uses tickets.
4. Price increase in price/cost simulator applies only to **Especialidades**.
5. Expense upload month overlap with sales; re-upload sales clears expenses.

## Rules

- **Unit tests are required** for logic/API/hook changes. Pre-commit and CI enforce **≥75%** backend coverage and **≥75%** frontend unit-surface coverage. Add tests; do not disable gates to “make it pass.”
- In **notebooks** (`backend/lab/`): create **new** cells; do not delete existing ones unless the user asks. Prefer **Plotly** for charts.
- Prefer extending `processing/engine.py` over bloating views.
- Match existing code style; small focused diffs; no drive-by refactors.
- Do not commit secrets; OAuth/DB stay env-driven and optional.

## Quality gate

```text
pre-commit: ruff → backend pytest+cov → eslint → frontend test:ci
CI (.github/workflows/test.yml): same idea on main/dev
```

Install once: `make dev-tools`.

## Related docs

| File | Role |
|------|------|
| [AGENTS.md](AGENTS.md) | Full agent context (structure, API, cheat sheet) |
| [README.md](README.md) | Product features + quick start |
| [docs/AUTH_AND_NEON.md](docs/AUTH_AND_NEON.md) | Optional auth/DB |
| [e2e/README.md](e2e/README.md) | Playwright |
