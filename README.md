# 🍕 Pizza EBITDA Simulator

A full-stack web application that calculates how many pizzas you need to sell to achieve at least 25% EBITDA margin.

## Features

- 📤 **Drag & Drop File Upload**: Upload sales and expenses Excel files
- 📊 **KPI Calculations**: Real-time EBITDA, margins, and cost analysis
- 🎯 **Simulation Mode**: Test how additional pizza sales affect your EBITDA
- 🔄 **Responsive Design**: Works on desktop and mobile

## Project Structure

```
omp/
├── backend/              # Django REST API
│   ├── manage.py
│   ├── requirements.txt
│   ├── pizza_simulator/  # Django settings
│   └── simulator/        # API endpoints & data processing
│       ├── data_processing.py  # sales_clean_up_data & kpi_calculations
│       ├── views.py
│       └── urls.py
├── frontend/             # React Application
│   ├── package.json
│   ├── public/
│   └── src/
│       ├── App.js       # Main application
│       ├── index.js
│       └── index.css
└── README.md
```

## Tech Stack

### Backend
- **Django 5.2+**: Web framework
- **Django REST Framework**: API endpoints
- **Pandas**: Data processing
- **OpenPyXL**: Excel file handling

### Frontend
- **React 18**: UI framework
- **React Dropzone**: File uploads
- **Axios**: HTTP client

## Prerequisites

- Python 3.10+
- Node.js 18+
- Excel files with the required structure

## Excel File Structure

### Sales File (Ventas)
Required sheet name: "Adiciones"
Required columns:
- Id. Venta
- Creación
- Producto
- Categoría
- Cantidad
- Precio
- Costo base
- Costo modificadores
- Costo total
- Creada por

### Expenses File (Gastos)
Required sheet name: "Gastos"
Required columns:
- Id
- Fecha
- Fecha de vencimiento
- Proveedor
- Categoría
- Subcategoría
- Comentario
- Estado del pago
- Importe
- Número Fiscal
- Tipo de comprobante
- N° de comprobante
- Creado por
- Cancelado

## Installation & Setup

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The backend will run on http://localhost:8000

### 2. Frontend Setup

```bash
cd frontend
npm install
npm start
```

The frontend will run on http://localhost:3000

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload-sales/` | POST | Upload sales Excel file |
| `/api/upload-expenses/` | POST | Upload expenses Excel file |
| `/api/products/` | GET | Get list of products |
| `/api/calculate/` | POST | Calculate KPIs with simulation |
| `/api/reset/` | POST | Reset all data |

## Usage

1. Open http://localhost:3000 in your browser
2. Upload your sales Excel file (Ventas)
3. Upload your expenses Excel file (Gastos)
4. Select a product from the dropdown
5. Enter the quantity of additional sales to simulate
6. Click "Calculate" to see the results
7. View your EBITDA and check if you've reached the 25% target

## Response Format

```json
{
  "ingresos": {
    "total_margen": 24949433,
    "total_ingreso": 39254935,
    "comision_total": 4504807,
    "costo_total": 14305502,
    "total_margen_sin_iva": 18681838
  },
  "gastos": {
    "gastos_totales": 30441308,
    "pagados_totales": 16982546,
    "por_pagar_totales": 13458762
  },
  "ebitda": {
    "ebitda": -11759470,
    "ebitda_percentage": -29.96
  }
}
```

## Development Notes

- The backend uses in-memory storage for uploaded data (resets on server restart)
- In production, consider using a proper database
- CORS is enabled for development purposes

## License

MIT License
