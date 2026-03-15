import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

// Configure axios base URL
axios.defaults.baseURL = 'http://localhost:8000';

// File Upload Component
const FileDropzone = ({ onDrop, title, description, uploaded, fileName }) => {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    multiple: false,
  });

  return (
    <div
      {...getRootProps()}
      className={`dropzone ${isDragActive ? 'active' : ''} ${uploaded ? 'uploaded' : ''}`}
    >
      <input {...getInputProps()} />
      <div className="dropzone-icon">{uploaded ? '✅' : '📁'}</div>
      <h3>{uploaded ? fileName || title : title}</h3>
      <p>{uploaded ? 'Archivo cargado correctamente' : description}</p>
    </div>
  );
};

// Results Display Component
const ResultsDisplay = ({ results }) => {
  if (!results) return null;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(value);
  };

  const isPositive = (value) => value >= 0;

  return (
    <div className="results-section">
      <h2>📊 Resultados</h2>
      <div className="results-grid">
        {/* Ingresos Card */}
        <div className="result-card">
          <h3>💰 Ingresos</h3>
          <div className="result-item">
            <span className="result-label">Total Ingreso</span>
            <span className="result-value">
              {formatCurrency(results.ingresos.total_ingreso)}
            </span>
          </div>
          <div className="result-item">
            <span className="result-label">Total Margen</span>
            <span className="result-value">
              {formatCurrency(results.ingresos.total_margen)}
            </span>
          </div>
          <div className="result-item">
            <span className="result-label">Comisión Total</span>
            <span className="result-value">
              {formatCurrency(results.ingresos.comision_total)}
            </span>
          </div>
          <div className="result-item">
            <span className="result-label">Costo Total</span>
            <span className="result-value">
              {formatCurrency(results.ingresos.costo_total)}
            </span>
          </div>
          <div className="result-item">
            <span className="result-label">Margen sin IVA</span>
            <span className="result-value">
              {formatCurrency(results.ingresos.total_margen_sin_iva)}
            </span>
          </div>
        </div>

        {/* Gastos Card */}
        <div className="result-card">
          <h3>💸 Gastos</h3>
          <div className="result-item">
            <span className="result-label">Gastos Totales</span>
            <span className="result-value">
              {formatCurrency(results.gastos.gastos_totales)}
            </span>
          </div>
          <div className="result-item">
            <span className="result-label">Pagados</span>
            <span className="result-value">
              {formatCurrency(results.gastos.pagados_totales)}
            </span>
          </div>
          <div className="result-item">
            <span className="result-label">Por Pagar</span>
            <span className="result-value">
              {formatCurrency(results.gastos.por_pagar_totales)}
            </span>
          </div>
        </div>

        {/* EBITDA Card */}
        <div className="result-card ebitda-card">
          <h3>📈 EBITDA</h3>
          <div className="result-item">
            <span className="result-label">EBITDA</span>
            <span className={`result-value ${isPositive(results.ebitda.ebitda) ? 'positive' : 'negative'}`}>
              {formatCurrency(results.ebitda.ebitda)}
            </span>
          </div>
          <div className="result-item">
            <span className="result-label">% EBITDA</span>
            <span className={`result-value ${isPositive(results.ebitda.ebitda_percentage) ? 'positive' : 'negative'}`}>
              {results.ebitda.ebitda_percentage}%
            </span>
          </div>
          <div className="result-item">
            <span className="result-label">Meta (25%)</span>
            <span className="result-value">
              {results.ebitda.ebitda_percentage >= 25 ? '✅ Alcanzada' : '❌ No alcanzada'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [salesFile, setSalesFile] = useState(null);
  const [expensesFile, setExpensesFile] = useState(null);
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [quantity, setQuantity] = useState(0);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Handle sales file upload
  const onSalesDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/api/upload-sales/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setSalesFile(file.name);
      setProducts(response.data.products);
      setSuccess('Archivo de ventas cargado correctamente');
    } catch (err) {
      setError(
        err.response?.data?.error ||
        'Error al cargar el archivo de ventas'
      );
      console.error('Upload error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Handle expenses file upload
  const onExpensesDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/api/upload-expenses/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setExpensesFile(file.name);
      setSuccess('Archivo de gastos cargado correctamente');
    } catch (err) {
      setError(
        err.response?.data?.error ||
        'Error al cargar el archivo de gastos'
      );
      console.error('Upload error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Handle calculation
  const handleCalculate = async () => {
    if (!selectedProduct || quantity < 0) {
      setError('Selecciona un producto y una cantidad válida');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post('/api/calculate/', {
        producto: selectedProduct,
        cantidad: parseInt(quantity, 10),
      });

      setResults(response.data);
    } catch (err) {
      setError(
        err.response?.data?.error ||
        'Error al calcular los KPIs'
      );
      console.error('Calculation error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle reset
  const handleReset = async () => {
    try {
      await axios.post('/api/reset/');
      setSalesFile(null);
      setExpensesFile(null);
      setProducts([]);
      setSelectedProduct('');
      setQuantity(0);
      setResults(null);
      setError(null);
      setSuccess('Datos reiniciados correctamente');
    } catch (err) {
      setError('Error al reiniciar los datos');
    }
  };

  const canCalculate = salesFile && expensesFile && selectedProduct;

  return (
    <div className="app">
      <header>
        <h1>🍕 Pizza EBITDA Simulator</h1>
        <p>
          Calcula cuántas pizzas necesitas vender para alcanzar al menos 25% de
          EBITDA
        </p>
      </header>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      {/* Upload Section */}
      <div className="upload-section">
        <FileDropzone
          onDrop={onSalesDrop}
          title="📥 Ventas"
          description="Arrastra tu archivo de ventas (Excel) aquí o haz clic para seleccionarlo"
          uploaded={!!salesFile}
          fileName={salesFile}
        />
        <FileDropzone
          onDrop={onExpensesDrop}
          title="📥 Gastos"
          description="Arrastra tu archivo de gastos (Excel) aquí o haz clic para seleccionarlo"
          uploaded={!!expensesFile}
          fileName={expensesFile}
        />
      </div>

      {/* Simulation Section */}
      {salesFile && products.length > 0 && (
        <div className="simulation-section">
          <h2>🎯 Simulación</h2>
          <div className="simulation-controls">
            <div className="form-group">
              <label htmlFor="product">Producto</label>
              <select
                id="product"
                value={selectedProduct}
                onChange={(e) => setSelectedProduct(e.target.value)}
              >
                <option value="">Selecciona un producto</option>
                {products.map((product, index) => (
                  <option key={index} value={product}>
                    {product}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="quantity">Cantidad adicional</label>
              <input
                type="number"
                id="quantity"
                min="0"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="0"
              />
            </div>
            <button
              className="btn-calculate"
              onClick={handleCalculate}
              disabled={!canCalculate || loading}
            >
              {loading ? 'Calculando...' : 'Calcular'}
            </button>
          </div>
        </div>
      )}

      {/* Results Section */}
      {results && <ResultsDisplay results={results} />}

      {/* Empty State */}
      {!salesFile && !expensesFile && !results && (
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <p>
            Carga tus archivos de ventas y gastos para comenzar la simulación
          </p>
        </div>
      )}

      {/* Reset Button */}
      {(salesFile || expensesFile || results) && (
        <div style={{ textAlign: 'center', marginTop: '30px' }}>
          <button
            onClick={handleReset}
            style={{
              padding: '10px 20px',
              backgroundColor: '#666',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
            }}
          >
            🔄 Reiniciar Todo
          </button>
        </div>
      )}
    </div>
  );
}

export default App;