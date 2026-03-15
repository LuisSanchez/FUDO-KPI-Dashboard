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
npm test          # Run tests
```

Backend only (from `backend/`):
```bash
python manage.py runserver   # Start Django server (port 8000)
```

## Architecture

### Backend (`backend/`)

- **`simulator/views.py`** — 5 API endpoints. Uses an in-memory dict `_session_data` to store uploaded file data between requests (no DB persistence; resets on server restart).
- **`simulator/data_processing.py`** — All business logic: data cleaning, KPI/EBITDA calculation, file validation, simulation row injection.
- **`pizza_simulator/settings.py`** — CORS allows all origins; SQLite for dev; media files in `backend/media/`.

API endpoints:
```
POST /api/upload-sales/     Upload sales Excel file ("Adiciones" sheet)
POST /api/upload-expenses/  Upload expenses Excel file ("Gastos" sheet)
GET  /api/products/         List unique products from uploaded sales
POST /api/calculate/        Run KPI/EBITDA calculation with optional simulation
POST /api/reset/            Clear in-memory session data
```

Key business logic in `data_processing.py`:
- `sales_clean_up_data()` — cleans data, computes `ingreso_sin_iva = ingreso / 1.19` (19% IVA), applies 30% commission deduction for Uber Eats orders
- `kpi_calculations()` — computes Ingresos, Gastos, and EBITDA
- `add_simulated_sales()` — appends simulated rows for what-if analysis; "Duo Familiar (2pizzas)" has special zero-modifier handling

### Frontend (`frontend/src/`)

- **`App.js`** — Single file containing all components: `FileDropzone`, `ResultsDisplay`, and `App`. State is managed at the `App` level.
- Proxies all `/api/` requests to `http://localhost:8000` (configured in `package.json`).
- Currency formatting uses Chilean Peso (CLP).

### Lab (`backend/lab/`)

Jupyter notebooks for data analysis. Per project rules: **create new cells, do not delete existing cells** unless explicitly requested. Use **Plotly** for interactive charts.

## Rules

- Do not add tests.
- In notebooks, create new cells rather than modifying/deleting existing ones.
- Prefer Plotly for charts in notebooks.
