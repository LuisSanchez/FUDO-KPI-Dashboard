# AGENTS.md — Agent / contributor context

Read this first. It is the only agent map of **OMP (FUDO Analytics)** — `CLAUDE.md` was retired into this file. Use it to navigate, change, and verify the codebase without rediscovering architecture.

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
├── AGENTS.md                 # This file — only agent onboarding doc
├── README.md                 # Product + quick start (humans)
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
│       ├── models.py         # UserSessionData, UserProfile, MonthAssumption
│       ├── report.py         # PDF (reportlab)
│       ├── data_processing.py# PUBLIC FACADE — re-exports engine API
│       ├── processing/
│       │   ├── constants.py  # UBER_COMMISSION_RATE = 0.25; collected 0.26
│       │   ├── engine.py     # Live KPI engine
│       │   ├── monthly.py    # Month rows from FUDO workbooks
│       │   └── uber_statements.py  # Page 1 of Uber monthly PDFs
│       ├── services/
│       │   ├── session_store.py  # pickle load/dump / clear store
│       │   └── month_history.py  # Saved months; adjustments are not written back
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
| Month history | `processing/monthly.py`, `processing/uber_statements.py`, `services/month_history.py` |
| Stable import path | `simulator/data_processing.py` (re-exports — keep for callers) |
| PDF | `simulator/report.py` |
| FE HTTP | `frontend/src/api/client.js` |
| FE upload/KPI state | `hooks/useSimulatorData.js` |
| FE auth | `hooks/useAuth.js` + `components/GoogleSignIn.js` |

When adding features: put logic in **engine** (live KPIs) or **monthly** (history), wire thin endpoints in **views**, reuse **data_processing** imports if existing code does. Avoid growing `views.py` with pandas.

Verified against the tree: live KPIs stay in `processing/engine.py`. Month history is `processing/monthly.py` plus `services/month_history.py`. Uber settlement PDFs are read by `processing/uber_statements.py` (pdfplumber, page 1 only). `data_processing.py` is still the re-export facade for the live engine. Do not look for a split `uber.py` / `cleaning.py` — those modules are gone. `pages/DashboardPage.js` re-exports `App.js`.

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
| GET | `history/` | Saved months. Payroll assumption and Uber PDF settlement are applied on the way out. `default_sueldos` is 1_300_000. |
| POST | `history/sueldos/` | Body `month` (`YYYY-MM`) and `sueldos` (replaces file payroll, 0 allowed) or `reset: true`. Stored on `MonthAssumption`, not the 24h session. |
| POST | `history/import-archive/` | Load `docs/2026` ventas + gastos into the session. Stored rows stay raw. |
| POST | `chat/` | Questions about the loaded numbers. OpenRouter tool loop over a local SQLite. 503 without `OPENROUTER_API_KEY`. |
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
3. **Uber commission** — see the cost model below. Do not regress it without an explicit product decision. `UBER_COMMISSION_RATE = 0.25` is applied only when `Creada por == "uber_eats"` (exact match).
4. **Break-even / 25% targets** — prefer **tickets** (`Id. Venta` unique), not loose unit counts, in simulators and PDF.
5. **Price simulator** — `price_increase_clp` applies only to **Especialidades**.
6. **Session** — re-uploading sales clears expenses; expenses months must overlap sales months.
7. **Proxy** — never set `axios.defaults.baseURL` in FE dev; use relative `/api` + `withCredentials`.
8. **Month history is a separate path.** It reads `Descuentos` and estimates Uber cash at 26% of what the customer paid. `DEFAULT_MONTH_SUELDOS` (1_300_000) replaces the file payroll for the month being evaluated; it is not added on top. Overrides live in `MonthAssumption`. Do not write that adjusted EBITDA back into `month_history`, and do not copy this formula into the live KPI engine.
9. **Uber settlement on the history screen** — show the 26% FUDO estimate beside the PDF (depósito, tasa, anuncios, ajustes). The P&L commission is the PDF “Tasas de servicio” line ÷ 1.19 when a statement exists (IVA on the fee is a credit, not a cost). The bank deposit is not the P&L cost. Do not change `UBER_COMMISSION_RATE`.

Formulas and scoring details are also summarized in `README.md` (promotion score, Uber break-even units/day).

### Uber Eats costs (checked 2026-10-11 on lab FUDO exports)

FUDO is the POS. Uber does not push its own cost file into this app. Sales come from sheet `Adiciones`; the fee is computed here.

What the exports show:

- `Precio` on `uber_eats` rows is the customer menu price, not the payout. Same products sell about 1.2–1.4× the local price. FUDO `Costo total` is always `Costo base + Costo modificadores` — the 25% fee is not in the file.
- Sheet `Pagos` for Uber tickets equals `Precio` minus sheet `Descuentos` (gap ≈ 0 across CG Feb–Apr 2026 and SM Oct 2025–Jan 2026). It is not net of commission. Uber discounts were 10–35% of Uber line prices; local discounts were small.
- Sheet `Gastos` in those same months has no Uber / marketplace commission invoice. EBITDA therefore never sees the fee.

What the code does today:

```text
comision            = Precio × 0.25          # KPI card shows this number
comision used in
  margen / Uber
  analysis          = comision / 1.19        # equals 25% of net sales
EBITDA              = ingreso_sin_iva − gastos operacionales
                      # commission is not subtracted
```

Those two commission figures are not the same expense. The constant comment treats 25% of gross as the net cost (IVA on Uber’s invoice is a recoverable crédito fiscal, so do not multiply by 1.19 and do not divide the 25% by 1.19 again). The margin and `/uber-eats/analysis/` paths divide by 1.19 anyway, which understates the fee versus that comment. EBITDA understates it further by omitting it.

Also not applied:

- `Descuentos` is never read, so Uber revenue and the 25% base use pre-discount line prices.
- `pedidos_ya` is treated as in-store (commission 0). `walker` / caja users too.
- Zero-cost imputation looks for `Categoría == "Extra"`. Live files use `Extras`, so the mask does not hit current exports. `Arma Tu Pizza` children are intentionally left at zero cost. A hardcoded Mar-2026 patch fills `Pizza Napoli` and `Pizza Veggie G` only.

Do not “fix” any of this silently. New monthly exports should be checked against `Pagos` and `Descuentos` before changing the rate or the base. The history screen already reads `Descuentos`; that does not authorize the same change in `engine.py`.

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
| Frontend unit | `frontend/src/**/__tests__`, `*.test.js` | **≥75%** statements/functions/lines, **≥70%** branches |
| E2E | `e2e/` | Optional; not required for pre-commit |
| Lint | ruff / eslint | Pre-commit + CI |

**Rules of engagement:**

- **Do add/update unit tests** when changing engine logic, APIs, or hooks. Pre-commit and CI enforce the coverage gates. Add tests; do not disable gates to make a change pass.
- **Do not** delete Jupyter notebook cells; append new cells; prefer **Plotly** in notebooks.
- Prefer extending `processing/engine.py` over bloating views. Match existing style; small diffs; no drive-by refactors.
- Do not force-push shared branches or rewrite published history unless explicitly asked.
- Do not commit secrets. OAuth and Postgres stay env-driven and off by default so Railway/SQLite deploys stay green (`docs/AUTH_AND_NEON.md`).

**Quality gate** (pre-commit, then CI on `main` / `dev`): ruff → backend pytest + coverage → eslint → frontend `test:ci`. Frontend thresholds are 75% statements, functions, and lines, and 70% branches. Install once with `make dev-tools`.

**Related docs:** [`README.md`](README.md) product overview, [`docs/AUTH_AND_NEON.md`](docs/AUTH_AND_NEON.md) optional auth/DB, [`e2e/README.md`](e2e/README.md) Playwright, [`Review-bugs.md`](Review-bugs.md) FUDO Uber cost-imputation notes.

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
| Month history / payroll assumption | `processing/monthly.py`, `services/month_history.py`, `components/MonthHistory.js` |
| Questions about the data | `services/analytics_db.py`, `services/openrouter_chat.py`, `components/DataChat.js` |
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
| `OPENROUTER_API_KEY` | empty | Chat. Empty returns 503. Server-side only |
| `OPENROUTER_MODEL` | `x-ai/grok-4.7` | OpenRouter model for the chat |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter API root |

Frontend Docker: `REACT_APP_BACKEND_URL=http://backend:8000` for proxy target.

---

## Out of scope unless requested

- Rewriting CRA → Next.js / Vite
- Making OAuth or Neon mandatory
- Dropping session/pickle model for a full multi-user data warehouse
- Deleting historical notebook cells or lab analyses
