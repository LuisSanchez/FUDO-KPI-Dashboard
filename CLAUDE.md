# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Pizza EBITDA Simulator — a full-stack web app to calculate EBITDA margins and simulate pizza sales scenarios. Django REST API backend + React 18 SPA frontend.

## Commands

Use `make` from the project root:

```bash
make dev          # Install all dependencies (backend + frontend)
make run          # Run both Django and React dev servers concurrently
make black        # Format Python code with Black
make migrations   # Create Django migrations
make migrate      # Apply Django migrations
make query        # Open Django shell
make lab          # Open Jupyter Lab
```

Frontend only (from `frontend/`):
```bash
npm start         # Start React dev server (port 3000)
npm run build     # Production build
```

Backend only (from `backend/`):
```bash
python manage.py runserver   # Start Django server (port 8000)
```

## Architecture

### Backend (`backend/`)

- **`simulator/views.py`** — API endpoints. Uses `UserSessionData` (SQLite) keyed by Django session cookie to store per-user uploaded file data. DataFrames are pickled into `BinaryField` columns. Sessions expire after 24 h (`SESSION_COOKIE_AGE`).
- **`simulator/models.py`** — `UserSessionData` model: `session_key`, `sales_df_pickle`, `expenses_df_pickle`, `products` (JSONField), `sales_months` (JSONField), `updated_at`.
- **`simulator/data_processing.py`** — All business logic: data cleaning, KPI/EBITDA calculation, file validation, chart data aggregation.
- **`pizza_simulator/settings.py`** — CORS allows all origins; SQLite for dev.

API endpoints (all prefixed `/api/`):
```
POST /api/upload-sales/        Upload sales Excel file ("Adiciones" sheet)
POST /api/upload-expenses/     Upload expenses Excel file ("Gastos" sheet, skiprows=3)
GET  /api/products/            List unique products from uploaded sales
POST /api/calculate/           Run KPI/EBITDA calculation with optional product/month filter
GET  /api/data/sales/          Per-product sales aggregation for table display
GET  /api/data/expenses/       Individual expense rows for table display
GET  /api/data/charts/         All chart datasets for the selected month
GET  /api/data/product-prices/ Per-product average pricing and margin breakdown
GET  /api/simulate/price-cost/ EBITDA simulation (?price_increase&cost_increase&month)
GET  /api/report/pdf/          Generate and download PDF financial report (?month=YYYY-MM)
GET  /api/report/excel/        Download Excel export (?categoria=Especialidades|Extras&month=YYYY-MM)
GET  /api/advisor/promotions/  Promotion recommendations (?month=YYYY-MM)
POST /api/reset/               Clear session data
```

Key business logic in `data_processing.py`:
- `sales_clean_up_data()` — cleans data, computes `ingreso_sin_iva = ingreso / 1.19` (19% IVA), applies 30% commission deduction for Uber Eats orders. Zero-cost patch: products with `Costo base = 0` are imputed from the max per-unit cost of the same product in the same period (targeted patch for "Pizza Napoli" / "Pizza Veggie G" in March 2026).
- `kpi_calculations()` — **EBITDA = `total_ingreso_sin_iva − gastos_totales`** (revenue minus all operational expenses from the expenses file; does NOT subtract FUDO COGS to avoid double-counting). Break-even and 25% target use **tickets** (unique `Id. Venta` count) not unit count: `avg_ticket = total_ingreso / total_tickets`; `breakeven_tickets = ceil(-ebitda / avg_contribution_per_ticket)`.
- `simulate_price_cost()` — returns baseline + projected metrics. Price increase applies only to Especialidades. Returns `avg_ticket_current/projected`, `contribution_pct_current/projected`, `date_from/date_to`, `total_tickets`.
- `get_chart_data()` — returns hourly, daily, and weekday count/revenue; top-10 by qty/revenue **split by category** (Especialidades / Extras); pie distribution; scatter (top 40).
- `get_product_prices_table()` — per-product average net price, IVA component, ingredient cost, margin breakdown, and `avg_precio_uber_eats` (separate average for Uber Eats channel).
- `get_sales_excel(df, categoria)` — returns xlsx bytes for all products in the given category with full margin columns (CMV%, Margen%, Comisión%).
- `get_promotion_advisor(df)` — top-5 products per category ranked by composite score: `score = margen_pct × 0.5 + (100 − cmv_pct) × 0.3 + volume_score × 0.2`. Returns hourly Uber Eats pattern and per-order avg ticket comparison.
- **`simulator/report.py`** — `build_financial_report(df_sales, df_expenses, month=None) -> bytes`. Reportlab PDF: cover with actual date range (`date_from – date_to`), KPI summary, break-even table (tickets-based, with wrapping Nota column), expenses breakdown, payables aging, and full product tables for **all** Especialidades and Extras (no cap).

Date validation: `upload_expenses` reads "Fecha" column, extracts months, and validates overlap with `sales_months` stored from `upload_sales`. Returns HTTP 422 `{"error": "date_mismatch"}` on no overlap. Re-uploading sales clears the stored expenses.

All numpy types must be explicitly cast to Python natives (`int()`, `float()`, `bool()`) before returning from views to avoid JSON serialization errors.

### Frontend (`frontend/src/`)

- **`App.js`** — Top-level state management. Handles file uploads, month selection, KPI display, and toast notifications. All sub-components are extracted; `App.js` only manages state and wires hooks.
- **`theme.js`** — MUI `createTheme` config (primary `#F97316`, background `#0F172A`, paper `#1E293B`).
- **`utils/formatters.js`** — Shared helpers: `CLP`, `PCT`, `CURRENT_MONTH`, `MONTH_NAMES`, `fmtMonth`, `cmvColor`, `TIPO_COLOR`.
- **`hooks/useDownloadPdf.js`** — `useDownloadPdf(selectedMonth, onError, months)`. Filename uses the actual data period: specific month → `reporte-{month}.pdf`; single available month → same; multiple → `reporte-{first}_a_{last}.pdf`.
- **`hooks/useDownloadExcel.js`** — `useDownloadExcel(selectedMonth, onError)`. `downloadExcel(categoria)` → `GET /api/report/excel/`.
- **`charts/`** — Chart.js chart components, one per file. All import shared config from `chartConfig.js`.
  - `ChartsSection.js` — Fetches `/api/data/charts/` and renders all charts. Full-width `SalesTrend` first, then 2-column grid. All charts support expand-to-modal via `OpenInFullIcon`.
  - `TopProductsByQuantity.js` / `TopProductsByRevenue.js` — Accept a `title` prop; rendered 4× (Especialidades qty, Especialidades rev, Extras qty, Extras rev).
- **`components/AppNavBar.js`** — "Descargar" dropdown: Reporte del Mes (PDF), Especialidades (Excel), Extras (Excel).
- **`components/SalesTableModal.js`** — Searchable (Producto + Categoría), sortable by any column, totals row reflects filtered data.
- **`components/ProductPricesModal.js`** — Sortable; filters by search, channel (all/uber_eats/local), and Categoría. Includes `avg_precio_uber_eats` column with delta chip.
- **`components/ExpensesTableModal.js`** — Filter chips for Tipo (Operacional/Préstamo/Activo Fijo). Sticky totals row.
- **`components/PriceCostSimulator.js`** — Sliders for price (+CLP, Especialidades only) and cost (+%). Shows date range of the calculation period, total tickets, and comparison table with rows: Ingreso s/IVA, CMV, Ticket promedio, Contribución %, EBITDA, EBITDA %, Precio prom. Especialidades.
- **`components/PromotionAdvisor.js`** — Collapsible. Fetches `GET /api/advisor/promotions/`. Shows top-5 Especialidades + top-5 Extras ranked by composite score, hourly Uber Eats bar chart, avg ticket comparison. ⓘ tooltip explains the scoring formula.
- **`components/HelpModal.js`** — `SECTIONS` data array; covers formulas, file requirements, tables/charts overview, and Asesor de Promociones section.
- **`components/ProjectionSimulator.js`** — Only renders when `isCurrentMonth`. Break-even and 25% target for remaining days.

Key frontend patterns:
- `CURRENT_MONTH = new Date().toISOString().slice(0, 7)` — used to gate the projection simulator
- `isCurrentMonth = selectedMonth === CURRENT_MONTH && months.includes(CURRENT_MONTH)`
- All `/api/` requests proxy to `http://localhost:8000` (configured in `package.json`)
- MUI dark theme: primary `#F97316`, background `#0F172A`, paper `#1E293B`
- Date mismatch on expense upload → `Snackbar` toast (HTTP 422), not an error alert
- Break-even uses **tickets** (`Id. Venta` unique count) as the unit of analysis throughout: simulator, report, and projection

### Lab (`backend/lab/`)

Jupyter notebooks for data analysis. Per project rules: **create new cells, do not delete existing cells** unless explicitly requested. Use **Plotly** for interactive charts.

## Rules

- Do not add tests.
- In notebooks, create new cells rather than modifying/deleting existing ones.
- Prefer Plotly for charts in notebooks.
