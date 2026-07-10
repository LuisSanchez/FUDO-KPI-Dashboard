# AGENTS.md — Agent / contributor context

Read this first. It is the canonical map of **OMP (FUDO Analytics)** so you can navigate, change, and verify the codebase without rediscovering architecture.

Human-facing product overview lives in [`README.md`](README.md). Optional auth/DB details: [`docs/AUTH_AND_NEON.md`](docs/AUTH_AND_NEON.md).

---

## What this product is

Full-stack **pizza franchise finance dashboard**. Owners upload FUDO POS Excel exports (sales + expenses), then see EBITDA, CMV, break-even, Uber Eats margins, promotions, Sunday viability, charts, and PDF/Excel exports.

- **Language of data / UI:** Spanish (column names, product labels, copy).
- **Persistence model:** Ephemeral **session** storage (pickled DataFrames, 24h). Not a multi-tenant ERP. Optional Google OAuth + Neon Postgres are **off by default** (Railway stays SQLite-safe).
- **Default git branch on GitHub:** `dev` (product default). Active integration branch for recent stack work: **`main`** (stack PRs were merged here). Prefer not inventing parallel long-lived stacks without asking.

---

## Stack (current)

| Layer | Tech |
|-------|------|
| Backend | Django **6.0**, DRF, Pandas, OpenPyXL, ReportLab, django-environ |
| DB | SQLite by default; optional `DATABASE_URL` → Postgres (Neon) |
| Frontend | React 18, MUI 7, Chart.js 4, Axios, CRA (`react-scripts` 5) |
| Unit tests | pytest + pytest-django + coverage (**≥75%**); Jest (**≥75%** on unit surface) |
| Lint | **Ruff** (backend), **ESLint** (frontend) |
| Quality gate | **pre-commit** (lint + unit tests + coverage) |
| E2E | Playwright under `e2e/` (optional; not in Docker/Railway image) |

---

## Repository layout

```
omp/
├── AGENTS.md                 # This file — agent onboarding
├── README.md                 # Product + quick start (humans)
├── CLAUDE.md                 # Claude Code pointer → mirrors AGENTS rules
├── Makefile                  # dev / test / docker entrypoints
├── .pre-commit-config.yaml   # ruff, eslint, coverage-gated unit tests
├── scripts/
│   ├── check-backend.sh      # pytest + coverage fail_under=75
│   └── check-frontend.sh     # Jest CI + coverage thresholds
├── docs/
│   ├── AUTH_AND_NEON.md      # Optional OAuth + DATABASE_URL
│   └── plans/                # Historical modernization notes
├── e2e/                      # Playwright (optional)
├── backend/
│   ├── manage.py
│   ├── requirements.txt      # runtime
│   ├── requirements-dev.txt  # pytest, ruff, black, pre-commit, cov
│   ├── pytest.ini            # cov enabled by default
│   ├── .coveragerc           # fail_under=75, omit migrations/tests
│   ├── ruff.toml
│   ├── pizza_simulator/      # Django project (settings, urls, wsgi)
│   ├── lab/                  # Jupyter notebooks (Plotly; never delete cells)
│   └── simulator/            # Django app
│       ├── views.py          # HTTP/API only — thin
│       ├── auth_views.py     # Google OAuth (optional)
│       ├── urls.py
│       ├── models.py         # UserSessionData, UserProfile
│       ├── report.py         # PDF (reportlab)
│       ├── data_processing.py# PUBLIC FACADE — re-exports engine API
│       ├── processing/
│       │   ├── constants.py  # UBER_COMMISSION_RATE = 0.25
│       │   └── engine.py     # ALL business logic lives here
│       ├── services/
│       │   └── session_store.py  # pickle load/dump / clear store
│       └── tests/            # unit + API tests
└── frontend/
    ├── package.json          # test:ci, lint, coverageThreshold
    └── src/
        ├── App.js            # Main shell: state wiring, layout
        ├── pages/DashboardPage.js  # Thin re-export of App (SoC shell)
        ├── api/client.js     # Axios API helpers (withCredentials)
        ├── hooks/            # useAuth, useSimulatorData, downloads, tour
        ├── utils/formatters.js
        ├── theme.js / ColorModeContext.js
        ├── charts/           # Chart.js components + ChartsSection
        ├── components/       # MUI sections/modals
        └── setupProxy.js     # /api → backend (do NOT set axios baseURL)
```

---

## Architecture (mental model)

```
Browser (React SPA :3000)
    │  relative /api/*  + session cookie
    ▼
CRA setupProxy  ──►  Django DRF (:8000)
                        │
                        ├─ views / auth_views     (HTTP, validation, status codes)
                        ├─ services/session_store (UserSessionData pickle I/O)
                        ├─ data_processing        (stable import facade)
                        │       └── processing/engine  (pure-ish pandas logic)
                        └─ report.py              (PDF bytes)
```

**Separation of concerns (already applied):**

| Concern | Module |
|---------|--------|
| HTTP | `simulator/views.py`, `auth_views.py` |
| Session DataFrames | `simulator/services/session_store.py` |
| Business logic | `simulator/processing/engine.py` (+ `constants.py`) |
| Stable import path | `simulator/data_processing.py` (re-exports — keep for callers) |
| PDF | `simulator/report.py` |
| FE HTTP | `frontend/src/api/client.js` |
| FE upload/KPI state | `hooks/useSimulatorData.js` |
| FE auth | `hooks/useAuth.js` + `components/GoogleSignIn.js` |

When adding features: put logic in **engine**, wire thin endpoints in **views**, reuse **data_processing** imports if existing code does. Avoid growing `views.py` with pandas.

---

## Commands

From repo root (prefer **Makefile** / **scripts**):

```bash
# Install
make dev              # runtime deps (backend requirements + frontend npm)
make dev-tools        # + requirements-dev, pre-commit install

# Run
make run              # Django :8000 + React :3000
# or:  make run-be / make run-fe

# Quality (also run by pre-commit)
make lint             # ruff + eslint
make test-be          # pytest + coverage ≥75%
make test-fe          # Jest unit + coverage ≥75%
make test             # both
make check            # lint + test

# Django
make migrate
make migrations
make query            # shell_plus
make lab              # Jupyter via shell_plus --lab

# Docker
# compose-up/down if defined in env; production single image:
make build / make up / make down
```

**Backend tests only:**
```bash
cd backend && ../.venv/bin/pytest
# Coverage gate is in .coveragerc (fail_under = 75)
```

**Frontend unit tests only:**
```bash
cd frontend && npm run test:ci   # CI=true, coverage thresholds in package.json
cd frontend && npm run lint
```

**E2E (optional):**
```bash
# servers up first
cd e2e && npm i && npx playwright install chromium && npm test
```

---

## API surface (`/api/`)

| Method | Path | Notes |
|--------|------|--------|
| POST | `upload-sales/` | Sheet `Adiciones` |
| POST | `upload-expenses/` | Sheet `Gastos`, `skiprows=3`; 422 `date_mismatch` if months don’t overlap sales |
| GET | `products/` | From session |
| POST | `calculate/` | KPIs; body `producto`, `month` |
| GET | `data/sales/` | Product aggregation |
| GET | `data/expenses/` | Expense rows |
| GET | `data/charts/` | Charts + `channel_split` + `channel_by_category` |
| GET | `data/product-prices/` | Pricing table |
| GET | `simulate/price-cost/` | `price_increase`, `cost_increase`, `month` |
| GET | `report/pdf/` | PDF download |
| GET | `report/excel/` | `categoria=Especialidades\|Extras` |
| GET | `advisor/promotions/` | Promotion scores |
| GET | `uber-eats/analysis/` | Margin + break-even |
| GET | `sunday-analysis/` | Sunday viability vs fixed cost buckets |
| POST | `reset/` | Clear session store |
| GET | `auth/config/` | `{ oauth_enabled, client_id, require_auth }` |
| GET | `auth/me/` | Session user or anonymous |
| POST | `auth/google/` | GIS credential (503 if OAuth off) |
| POST | `auth/logout/` | |

All numpy/pandas scalars returned from views must be cast to Python `int` / `float` / `bool` for JSON.

---

## Business rules agents must not break

1. **EBITDA** = `total_ingreso_sin_iva − gastos_operacionales`
   - Gastos from expenses file already include materia prima → **do not** also subtract FUDO line-item COGS into EBITDA.
   - Exclude loans (`Proveedor` ~ Prestamo) and CapEx (`Categoría == Activo Fijo`); ignore `Cancelado == "Si"`.
2. **IVA 19%** — analysis net of IVA (`/ 1.19`).
3. **Uber commission** — `UBER_COMMISSION_RATE = 0.25` on gross for `Creada por == uber_eats` (IVA on commission recoverable).
4. **Break-even / 25% targets** — prefer **tickets** (`Id. Venta` unique), not loose unit counts, in simulators and PDF.
5. **Price simulator** — `price_increase_clp` applies only to **Especialidades**.
6. **Session** — re-uploading sales clears expenses; expenses months must overlap sales months.
7. **Proxy** — never set `axios.defaults.baseURL` in FE dev; use relative `/api` + `withCredentials`.

Formulas and scoring details are also summarized in `README.md` (promotion score, Uber break-even units/day).

---

## Frontend patterns

- **Theme:** primary `#F97316`; dark paper `#1E293B` / bg `#0F172A` (light mode also supported via `ColorModeContext`).
- **Month gate:** `CURRENT_MONTH` from `formatters.js`; projection simulator only when selected month is current and present in data.
- **Uploads / KPI state:** prefer extending `useSimulatorData` rather than duplicating state in random components.
- **Charts:** `ChartsSection` fetches once; can bubble `onChartData` to `App` for Uber Eats channel charts.
- **Unit-test surface (coverage gate):** `src/utils`, `src/hooks`, `src/api`, `src/theme.js`, `src/ColorModeContext.js`, `src/pages` — not every chart/component. UI chrome is covered lightly or via e2e.

---

## Testing & quality expectations

| Kind | Location | Gate |
|------|----------|------|
| Backend unit/API | `backend/simulator/tests/` | Coverage **≥75%** of `simulator` (omit migrations/tests) |
| Frontend unit | `frontend/src/**/__tests__`, `*.test.js` | **≥75%** on collectCoverageFrom paths |
| E2E | `e2e/` | Optional; not required for pre-commit |
| Lint | ruff / eslint | Pre-commit + CI |

**Rules of engagement:**

- **Do add/update unit tests** when changing engine logic, APIs, or hooks — pre-commit will fail under 75%.
- **Do not** delete Jupyter notebook cells; append new cells; prefer **Plotly** in notebooks.
- Prefer small, focused PRs; keep views thin.
- Do not force-push shared branches or rewrite published history unless explicitly asked.
- Optional Neon/OAuth: keep defaults off so Railway/SQLite deploys stay green (`docs/AUTH_AND_NEON.md`).

---

## CI

[`.github/workflows/test.yml`](.github/workflows/test.yml):

- Triggers: push/PR to `main` and `dev` (and `stack/**` pushes).
- **backend** job: migrate (SQLite) → ruff → pytest (coverage).
- **frontend** job: eslint → `npm run test:ci`.

---

## Where to change what (cheat sheet)

| Task | Start here |
|------|------------|
| New KPI / cleaning rule | `processing/engine.py` + unit test |
| New API endpoint | `views.py` + `urls.py` + API test |
| Session storage | `services/session_store.py` |
| PDF layout | `report.py` |
| FE API call | `api/client.js` |
| Upload/month/KPI state | `hooks/useSimulatorData.js` |
| Auth UI | `hooks/useAuth.js`, `GoogleSignIn.js` |
| Chart | `charts/*` + often `get_chart_data` in engine |
| Theme / formatters | `theme.js`, `utils/formatters.js` |
| Coverage / pre-commit | `.coveragerc`, `package.json` jest, `.pre-commit-config.yaml` |

---

## Environment variables (backend)

| Var | Default | Purpose |
|-----|---------|---------|
| `DEBUG` | false | Django debug |
| `SECRET_KEY` | dev insecure default | Django secret |
| `DATABASE_URL` | empty → SQLite | Neon/Postgres |
| `GOOGLE_OAUTH_ENABLED` | false | Enable GIS login |
| `GOOGLE_CLIENT_ID` | empty | OAuth client |
| `REQUIRE_AUTH` | false | Hard-gate APIs (use carefully) |

Frontend Docker: `REACT_APP_BACKEND_URL=http://backend:8000` for proxy target.

---

## Out of scope unless requested

- Rewriting CRA → Next.js / Vite
- Making OAuth or Neon mandatory
- Dropping session/pickle model for a full multi-user data warehouse
- Deleting historical notebook cells or lab analyses
