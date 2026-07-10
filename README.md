# FUDO Analytics — Pizza Finance Dashboard

Full-stack app that analyzes pizza store profitability from **FUDO** POS Excel exports. Calculates EBITDA, CMV, and break-even; simulates price/cost and volume targets; deep-dives Uber Eats and Sunday viability; exports PDF/Excel.

> **Agents / contributors:** start with [`AGENTS.md`](AGENTS.md) for architecture, commands, and coding rules.

## Features

- **Drag & drop upload** — Sales (`Adiciones`) and expenses (`Gastos`) Excel files
- **KPI dashboard** — EBITDA, CMV%, margins, operational vs loans vs CapEx
- **Break-even & projection** — Ticket-based targets (EBITDA = 0 and 25%); current-month daily pace
- **Price / cost simulator** — Price delta on Especialidades only; cost % on ingredients
- **Charts** — Trend, hour/weekday, top products by category, distribution, scatter, channel split
- **Uber Eats analysis** — Margin after 25% commission, channel KPIs, break-even units/day
- **Sunday analysis** — Viability vs fixed-cost buckets (arriendo, personal, etc.)
- **Promotion advisor** — Ranked products by margin / CMV / volume score
- **Tables** — Searchable sales, expenses (tipo chips), product prices (Uber column)
- **Exports** — PDF financial report; Excel Especialidades / Extras
- **Optional auth** — Google Sign-In + Neon Postgres (off by default; see [docs/AUTH_AND_NEON.md](docs/AUTH_AND_NEON.md))
- **Theme** — Dark / light MUI theme

## Project structure

```
omp/
├── AGENTS.md                 # Agent onboarding (architecture map)
├── Makefile                  # dev, test, docker
├── scripts/check-*.sh        # coverage-gated unit tests
├── backend/
│   ├── pizza_simulator/      # Django settings / root urls
│   └── simulator/
│       ├── views.py          # API (thin)
│       ├── auth_views.py     # Optional Google OAuth
│       ├── data_processing.py# Facade → processing.engine
│       ├── processing/       # Business logic (engine + constants)
│       ├── services/         # Session pickle store
│       ├── report.py         # PDF
│       ├── models.py         # UserSessionData, UserProfile
│       └── tests/            # pytest (coverage ≥75%)
├── frontend/src/
│   ├── App.js / pages/       # Shell
│   ├── api/client.js         # Axios (withCredentials)
│   ├── hooks/                # useSimulatorData, useAuth, downloads
│   ├── charts/ · components/
│   └── utils/formatters.js
├── e2e/                      # Playwright (optional)
└── docs/                     # Auth/Neon + plans
```

## Tech stack

| Area | Choice |
|------|--------|
| Backend | Django 6 + DRF, Pandas, ReportLab, SQLite (optional Postgres) |
| Frontend | React 18, MUI 7, Chart.js 4, CRA |
| Quality | Ruff, ESLint, pytest-cov ≥75%, Jest ≥75%, pre-commit |
| Deploy shape | Docker multi-stage (SPA via WhiteNoise) or Railway-friendly SQLite |

## Prerequisites

- Python **3.12** recommended (Django 6)
- Node.js **18+** (20 in CI/Docker)
- FUDO export access

## Quick start

```bash
make dev          # Install runtime deps
make dev-tools    # Optional: test/lint/pre-commit tooling
make run          # API :8000 + UI :3000
```

```bash
make check        # Lint + unit tests with coverage gates
```

### Docker

```bash
# Live-reload compose (if using docker-compose.yml)
docker compose up

# Production-style single image
make build && make up
```

### Excel requirements

**Sales — sheet `Adiciones`:**
`Id. Venta`, `Creación`, `Producto`, `Categoría`, `Cantidad`, `Precio`, `Costo base`, `Costo modificadores`, `Costo total`, `Creada por`

**Expenses — sheet `Gastos` (data from row 4):**
`Id`, `Fecha`, `Fecha de vencimiento`, `Proveedor`, `Categoría`, `Subcategoría`, `Comentario`, `Estado del pago`, `Importe`, `Número Fiscal`, `Tipo de comprobante`, `N° de comprobante`, `Creado por`, `Cancelado`

## API (prefix `/api/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload-sales/` | Upload sales Excel |
| POST | `/upload-expenses/` | Upload expenses (422 if month mismatch) |
| GET | `/products/` | Unique products |
| POST | `/calculate/` | KPIs (`producto`, `month`) |
| GET | `/data/sales/` | Sales table aggregation |
| GET | `/data/expenses/` | Expense rows |
| GET | `/data/charts/` | Charts + channel split |
| GET | `/data/product-prices/` | Pricing / margins |
| GET | `/simulate/price-cost/` | Price & cost simulation |
| GET | `/report/pdf/` | PDF report |
| GET | `/report/excel/` | Category Excel export |
| GET | `/advisor/promotions/` | Promotion recommendations |
| GET | `/uber-eats/analysis/` | Uber Eats analysis |
| GET | `/sunday-analysis/` | Sunday viability |
| POST | `/reset/` | Clear session |
| GET | `/auth/config/` | OAuth flags for SPA |
| GET | `/auth/me/` | Current user |
| POST | `/auth/google/` | GIS login |
| POST | `/auth/logout/` | Logout |

## Key business logic

**EBITDA:**
```text
EBITDA = Ingresos sin IVA − Gastos operacionales
```
Operational expenses already include ingredient purchases (Materia Prima). Do **not** subtract FUDO line COGS again. Loans and CapEx are excluded.

**IVA:** All analysis is net of 19% IVA.

**Tickets (not loose units) for break-even / 25% targets:**
```text
avg_ticket          = total_ingreso_sin_iva / unique(Id. Venta)
contribution/ticket = avg_ticket − avg_CMV/ticket
breakeven_tickets   = ceil(−EBITDA / contribution_per_ticket)
```

**Uber Eats commission:** `UBER_COMMISSION_RATE = 0.25` on gross for Uber rows (commission IVA recoverable).

**Price simulator:** price increase applies only to **Especialidades**.

**Promotion score:**
```text
score = margen_pct × 0.5 + (100 − cmv_pct) × 0.3 + volume_score × 0.2
```

Full agent-oriented detail: [`AGENTS.md`](AGENTS.md).

## Development notes

- Session data in SQLite (`UserSessionData`), 24h cookie age; DataFrames pickled in `BinaryField`
- FE proxies `/api` through `setupProxy.js` — **do not** set `axios.defaults.baseURL` in development
- Cast numpy types to Python natives before JSON responses
- Pre-commit runs ruff, eslint, and coverage-gated unit tests on commit (`make dev-tools`)

## License / use

Internal franchise analytics tool. Data remains in the browser session unless optional auth/DB is enabled.
