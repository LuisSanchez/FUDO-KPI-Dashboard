# FUDO Analytics — Pizza Finance Dashboard

A full-stack web application that analyzes pizza store profitability using FUDO export files. Calculates EBITDA, CMV, and break-even points, and simulates how many additional units you need to sell to reach target margins.

## Features

- **Drag & Drop Upload** — Sales (`Adiciones` sheet) and expenses (`Gastos` sheet) Excel files
- **KPI Dashboard** — Real-time EBITDA, CMV%, margins, and expense breakdown (operational vs. loans vs. CapEx)
- **Break-even Simulator** — Per-ticket simulation showing tickets needed for EBITDA = 0 and EBITDA = 25%
- **Projection Simulator** — Current-month projection: daily sales pace needed to close the gap before month end
- **Visual Analytics** — Charts by category (Especialidades / Extras): daily trend with 7-day rolling average, by-hour, by-weekday, top products by category, distribution, and scatter
- **Channel Split Charts** — Doughnut (units & revenue: Uber Eats vs Local) and grouped bar (Especialidades × Extras × channel)
- **Uber Eats Analysis** — Per-product margin after 25% commission (green = profitable, red = losing money); channel KPI strip; break-even volume in units/day using operational fixed costs
- **Data Tables** — Searchable, sortable tables for sales by product and category; expense detail with type filter; per-product pricing with Uber Eats price column, channel filter, and category filter
- **Promotion Advisor** — Data-driven Uber Eats promotion recommendations: top 5 products per category ranked by composite score (margin, cost efficiency, volume), hourly activity heatmap, and average ticket comparison
- **Exports** — "Descargar" dropdown: PDF financial report, Excel for Especialidades, Excel for Extras (all products, full margin breakdown)
- **Responsive Navbar** — On small screens, table buttons collapse to icon-only; "Descargar" becomes a download icon

## Project Structure

```
omp/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── pizza_simulator/       # Django settings
│   └── simulator/
│       ├── data_processing.py # Business logic: cleaning, KPIs, chart data
│       ├── report.py          # PDF report generator (reportlab)
│       ├── views.py           # API endpoints
│       ├── urls.py
│       └── models.py          # UserSessionData (SQLite, session-keyed)
├── frontend/
│   ├── package.json
│   └── src/
│       ├── App.js             # Top-level state & layout
│       ├── charts/
│       │   ├── chartConfig.js
│       │   ├── ChartsSection.js
│       │   ├── SalesTrend.js           # Full-width daily trend + rolling average
│       │   ├── SalesByDay.js / SalesByWeekday.js
│       │   ├── SalesByHour.js / RevenueByHour.js
│       │   ├── TopProductsByQuantity.js / TopProductsByRevenue.js
│       │   ├── ProductDistribution.js
│       │   ├── QuantityVsRevenue.js
│       │   ├── ChannelSplitChart.js    # Doughnuts: Uber Eats vs Local
│       │   ├── ChannelByCategoryChart.js # Grouped bar: category × channel
│       │   └── UberEatsMarginChart.js  # Margin% per product on Uber Eats
│       ├── hooks/
│       │   ├── useDownloadPdf.js
│       │   ├── useDownloadExcel.js
│       │   └── useTour.js
│       ├── utils/
│       │   └── formatters.js        # CLP, PCT, fmtMonth, cmvColor, CURRENT_MONTH
│       ├── theme.js                 # MUI dark theme
│       └── components/
│           ├── AppNavBar.js         # Responsive: icon-only on mobile
│           ├── DropzoneCard.js
│           ├── EbitdaGauge.js
│           ├── ExpensesTableModal.js
│           ├── HelpModal.js
│           ├── KpiRow.js
│           ├── PriceCostSimulator.js
│           ├── ProductPricesModal.js
│           ├── ProjectionSimulator.js
│           ├── PromotionAdvisor.js   # Uber Eats promotion recommendations
│           ├── SalesTableModal.js
│           ├── SimCard.js
│           └── UberEatsSection.js   # Channel charts + margin + break-even
└── README.md
```

## Tech Stack

### Backend
- **Django 5.2** + **Django REST Framework**
- **Pandas** — data cleaning and aggregation
- **OpenPyXL / xlrd** — Excel file parsing
- **ReportLab** — PDF generation
- **SQLite** — session data storage (dev)

### Frontend
- **React 18** + **MUI v5** (dark theme)
- **Chart.js 4** + **react-chartjs-2** — all charts
- **React Dropzone** — file uploads
- **Axios** — HTTP client

## Prerequisites

- Python 3.10+
- Node.js 18+
- FUDO account with export access

## Quick Start

### Local development
```bash
make dev   # Install dependencies
make run   # Run Django (8000) + React (3000) concurrently
```

### Docker (live reload)
```bash
make compose-up   # Both services with hot reload
```

### Docker (production image)
```bash
make build   # Build & run single-image Docker container on port 8000
```

## Excel File Requirements

### Sales file — sheet `Adiciones`
Required columns: `Id. Venta`, `Creación`, `Producto`, `Categoría`, `Cantidad`, `Precio`, `Costo base`, `Costo modificadores`, `Costo total`, `Creada por`

### Expenses file — sheet `Gastos` (data starts row 4)
Required columns: `Id`, `Fecha`, `Fecha de vencimiento`, `Proveedor`, `Categoría`, `Subcategoría`, `Comentario`, `Estado del pago`, `Importe`, `Número Fiscal`, `Tipo de comprobante`, `N° de comprobante`, `Creado por`, `Cancelado`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload-sales/` | Upload sales Excel |
| POST | `/api/upload-expenses/` | Upload expenses Excel |
| GET | `/api/products/` | List unique products |
| POST | `/api/calculate/` | KPI/EBITDA calculation (`producto`, `month`) |
| GET | `/api/data/sales/` | Per-product sales table |
| GET | `/api/data/expenses/` | Expense detail table |
| GET | `/api/data/charts/` | All chart datasets (incl. channel split by category) |
| GET | `/api/data/product-prices/` | Per-product pricing & margins (incl. Uber Eats avg price) |
| GET | `/api/simulate/price-cost/` | EBITDA simulation (`?price_increase&cost_increase&month`) |
| GET | `/api/report/pdf/` | Download PDF report (`?month=YYYY-MM`) |
| GET | `/api/report/excel/` | Download Excel export (`?categoria=Especialidades\|Extras&month=YYYY-MM`) |
| GET | `/api/advisor/promotions/` | Promotion recommendations (`?month=YYYY-MM`) |
| GET | `/api/uber-eats/analysis/` | Uber Eats margin + break-even analysis (`?month=YYYY-MM`) |
| POST | `/api/reset/` | Clear session data |

## Key Business Logic

**EBITDA formula:**
```
EBITDA = Ingresos sin IVA − Gastos operacionales
```
Gastos operacionales come from the FUDO expenses file and already include ingredient purchases (Materia Prima). FUDO COGS are **not** subtracted separately to avoid double-counting. Loans and CapEx purchases are excluded.

**Break-even:**
```
x = −EBITDA / avg_margin_per_unit
```

**25% EBITDA target:**
```
x = (0.25·I − E) / (m − 0.25·i)
```
where `E` = current EBITDA, `I` = current revenue, `m` = margin/unit, `i` = revenue/unit.

**IVA (19%):** All analysis is net of IVA. Cash register amounts = net value × 1.19.

**Break-even and 25% EBITDA target use tickets, not units:**
```
avg_ticket           = total_ingreso_sin_iva / unique(Id. Venta)
contribution/ticket  = avg_ticket − avg_CMV/ticket
breakeven_tickets    = ceil(−EBITDA / contribution_per_ticket)
25% target tickets   = (0.25·I − EBITDA) / (contribution − 0.25·avg_ticket)
```
The simulator and the PDF report both use this ticket-based model. The `PriceCostSimulator` component exposes `avg_ticket` and `contribution_pct` in its comparison table.

**Price/cost simulator scope:** The `price_increase_clp` delta is applied only to Especialidades. The response includes `date_from`, `date_to`, `total_tickets`, `avg_ticket_current/projected`, and `contribution_pct_current/projected`.

**Zero-cost imputation:** Products with cost = 0 are patched by the highest available per-unit cost of the same product in the same period. A targeted patch covers "Pizza Napoli" and "Pizza Veggie G" for March 2026.

**PDF report filename:** Derived from actual data period — single month → `reporte-YYYY-MM.pdf`; multiple months → `reporte-YYYY-MM_a_YYYY-MM.pdf`. Applied in both the backend `Content-Disposition` header and the frontend download hook.

**Uber Eats commission:**
```
UBER_COMMISSION_RATE = 0.25   (25% of gross sale price)
```
Uber Eats charges 25% + IVA (19%) on the net price. Since IVA on the commission is a recoverable input credit for the restaurant, the net effective rate on the gross sale is 25%. Applied in `sales_clean_up_data` and `get_uber_eats_analysis`.

**Uber Eats break-even (units/day):**
```
contribution_per_unit = avg_price_sin_iva − avg_ingredient_cost − avg_commission_sin_iva
breakeven_units_total = fixed_costs / contribution_per_unit
breakeven_per_day     = breakeven_units_total / days_in_period
```

**Channel split data** (returned by `/api/data/charts/`):
- `channel_split`: `{labels, units, revenue}` — Uber Eats vs Local totals
- `channel_by_category`: `{Especialidades: {Uber Eats: {units, revenue}, Local: ...}, Extras: {...}}`

**Promotion advisor scoring:**
```
score = margen_pct × 0.5 + (100 − cmv_pct) × 0.3 + volume_score × 0.2
```
- `volume_score` = (product qty / max qty in category) × 100, capped at 100
- Products with fewer than 3 units sold or CMV = 0 are excluded
- Top 5 per category (Especialidades, Extras) are returned

## Docker Notes

- `docker-compose.yml` — development setup with bind-mount volumes for live reload. `CHOKIDAR_USEPOLLING=true` enables file watching inside Docker on macOS.
- `setupProxy.js` — proxies `/api` to `REACT_APP_BACKEND_URL` (Docker: `http://backend:8000`) or `http://localhost:8000` locally. **Do not set `axios.defaults.baseURL`** — it bypasses the proxy and breaks session cookies.
- Production image (`Dockerfile`) — multi-stage build: React compiled to static files served by Django via WhiteNoise.

## Development Notes

- Session data is stored in SQLite keyed by Django session cookie and expires after 24 h
- CORS is open for all origins in dev (`CORS_ALLOW_ALL_ORIGINS = True`)
- All numpy types are cast to Python natives before JSON serialization
