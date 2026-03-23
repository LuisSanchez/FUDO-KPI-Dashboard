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
POST /api/upload-sales/       Upload sales Excel file ("Adiciones" sheet)
POST /api/upload-expenses/    Upload expenses Excel file ("Gastos" sheet, skiprows=3)
GET  /api/products/           List unique products from uploaded sales
POST /api/calculate/          Run KPI/EBITDA calculation with optional product/month filter
GET  /api/data/sales/         Per-product sales aggregation for table display
GET  /api/data/expenses/      Individual expense rows for table display
GET  /api/data/charts/        All chart datasets for the selected month
POST /api/reset/              Clear in-memory session data
```

Key business logic in `data_processing.py`:
- `sales_clean_up_data()` — cleans data, computes `ingreso_sin_iva = ingreso / 1.19` (19% IVA), applies 30% commission deduction for Uber Eats orders
- `kpi_calculations()` — computes Ingresos, Gastos, and EBITDA; simulation dict includes `current_units`, `breakeven_units`, `target_25_units`, `total_for_breakeven`, `total_for_25pct`
- `get_chart_data()` — returns hourly count/revenue, top-10 by qty/revenue, pie distribution, scatter (top 40)
- `add_simulated_sales()` — appends simulated rows for what-if analysis; "Duo Familiar (2pizzas)" has special zero-modifier handling

Date validation: `upload_expenses` reads "Fecha" column, extracts months, and validates overlap with `sales_months` stored from `upload_sales`. Returns HTTP 422 `{"error": "date_mismatch"}` on no overlap. Re-uploading sales clears the stored expenses.

All numpy types must be explicitly cast to Python natives (`int()`, `float()`, `bool()`) before returning from views to avoid JSON serialization errors.

### Frontend (`frontend/src/`)

- **`App.js`** — Top-level state management. Contains `FileDropzone` and `ResultsDisplay` components inline. Handles file uploads, month selection, KPI display, and toast notifications.
- **`charts/`** — Chart.js chart components, one per file. All import shared config from `chartConfig.js`.
  - `chartConfig.js` — Central Chart.js registration (must import before any chart renders), shared theme constants (`COLORS`, `PALETTE`), base option objects (`baseOptions`, `horizontalBaseOptions`), and `CLP` formatter.
  - `ChartsSection.js` — Fetches `/api/data/charts/` and renders all 6 charts. Charts support expand-to-modal via `OpenInFullIcon`.
- **`components/ProjectionSimulator.js`** — "How much do I need to sell?" simulator. Only renders when `isCurrentMonth && salesLoaded && expensesLoaded`. Uses per-unit averages from `/api/calculate/` response to compute breakeven and 25% EBITDA targets for remaining days in the month.

Key frontend patterns:
- `CURRENT_MONTH = new Date().toISOString().slice(0, 7)` — used to gate the projection simulator
- `isCurrentMonth = selectedMonth === CURRENT_MONTH && months.includes(CURRENT_MONTH)`
- All `/api/` requests proxy to `http://localhost:8000` (configured in `package.json`)
- MUI dark theme: primary `#F97316`, background `#0F172A`, paper `#1E293B`
- Date mismatch on expense upload → `Snackbar` toast (HTTP 422), not an error alert

### Lab (`backend/lab/`)

Jupyter notebooks for data analysis. Per project rules: **create new cells, do not delete existing cells** unless explicitly requested. Use **Plotly** for interactive charts.

## Rules

- Do not add tests.
- In notebooks, create new cells rather than modifying/deleting existing ones.
- Prefer Plotly for charts in notebooks.
