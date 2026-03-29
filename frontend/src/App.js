import React, { useState, useCallback, useEffect } from "react";
import axios from "axios";
import ChartsSection from "./charts/ChartsSection";
import HelpModal from "./components/HelpModal";
import AppNavBar from "./components/AppNavBar";
import ProjectionSimulator from "./components/ProjectionSimulator";
import PriceCostSimulator from "./components/PriceCostSimulator";
import KpiRow from "./components/KpiRow";
import DropzoneCard from "./components/DropzoneCard";
import EbitdaGauge from "./components/EbitdaGauge";
import SimCard from "./components/SimCard";
import SalesTableModal from "./components/SalesTableModal";
import ExpensesTableModal from "./components/ExpensesTableModal";
import ProductPricesModal from "./components/ProductPricesModal";
import { useTour } from "./hooks/useTour";
import useDownloadPdf from "./hooks/useDownloadPdf";
import { CLP, fmtMonth, CURRENT_MONTH, cmvColor } from "./utils/formatters";
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Container,
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  Autocomplete,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Chip,
  Alert,
  Snackbar,
  LinearProgress,
  Divider,
} from "@mui/material";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import BalanceIcon from "@mui/icons-material/Balance";
import LocalPizzaIcon from "@mui/icons-material/LocalPizza";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";

if (process.env.NODE_ENV === "development") {
  axios.defaults.baseURL = "http://localhost:8000";
}

// ── Theme ─────────────────────────────────────────────────────────────────────
const theme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#F97316" },
    secondary: { main: "#94A3B8" },
    success: { main: "#22C55E" },
    error: { main: "#EF4444" },
    warning: { main: "#FBBF24" },
    background: { default: "#0F172A", paper: "#1E293B" },
    text: { primary: "#F1F5F9", secondary: "#94A3B8" },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", sans-serif',
    h4: { fontWeight: 700 },
    h6: { fontWeight: 600 },
    subtitle2: {
      fontWeight: 600,
      color: "#94A3B8",
      textTransform: "uppercase",
      letterSpacing: "0.08em",
      fontSize: "0.7rem",
    },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiPaper: { styleOverrides: { root: { backgroundImage: "none" } } },
    MuiDialog: {
      styleOverrides: {
        paper: { backgroundImage: "none", bgcolor: "#1E293B" },
      },
    },
    MuiToggleButton: {
      styleOverrides: {
        root: {
          border: "1px solid #334155",
          color: "#94A3B8",
          textTransform: "none",
          "&.Mui-selected": {
            backgroundColor: "#F9731620",
            color: "#F97316",
            borderColor: "#F97316",
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: { borderColor: "#334155" },
        head: {
          fontWeight: 600,
          color: "#94A3B8",
          fontSize: "0.72rem",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          backgroundColor: "#0F172A",
        },
      },
    },
  },
});

// ── Main App ──────────────────────────────────────────────────────────────────

export default function App() {
  const [salesFile, setSalesFile] = useState(null);
  const [expensesFile, setExpensesFile] = useState(null);
  const [months, setMonths] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState("all");
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [helpOpen, setHelpOpen] = useState(false);
  const [salesTableOpen, setSalesTableOpen] = useState(false);
  const [expensesTableOpen, setExpensesTableOpen] = useState(false);
  const [pricesTableOpen, setPricesTableOpen] = useState(false);
  const [salesTableData, setSalesTableData] = useState([]);
  const [expensesTableData, setExpensesTableData] = useState([]);
  const [pricesTableData, setPricesTableData] = useState([]);
  const [toast, setToast] = useState({ open: false, message: "" });

  const bothUploaded = !!(salesFile && expensesFile);

  const { startTour } = useTour(bothUploaded);
  const { handleDownloadPdf, pdfLoading } = useDownloadPdf(
    selectedMonth,
    (msg) => setToast({ open: true, message: msg }),
  );

  // ── Calculate KPIs ─────────────────────────────────────────────────────────
  const calculate = useCallback(
    async (month, product) => {
      if (!salesFile || !expensesFile) return;
      setLoading(true);
      setError(null);
      try {
        const body = {};
        if (month && month !== "all") body.month = month;
        if (product) body.producto = product;
        const res = await axios.post("/api/calculate/", body);
        setResults(res.data);
      } catch (err) {
        setError(err.response?.data?.error || "Error al calcular los KPIs");
      } finally {
        setLoading(false);
      }
    },
    [salesFile, expensesFile],
  );

  // Auto-calculate once both files are ready
  useEffect(() => {
    if (bothUploaded) calculate(selectedMonth, selectedProduct);
  }, [bothUploaded]); // eslint-disable-line

  // ── Upload handlers ────────────────────────────────────────────────────────
  const onSalesDrop = useCallback(
    async (files) => {
      const file = files[0];
      if (!file) return;
      setLoading(true);
      setError(null);
      const fd = new FormData();
      fd.append("file", file);
      try {
        const res = await axios.post("/api/upload-sales/", fd, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setSalesFile(file.name);
        setProducts(res.data.products || []);
        setMonths(res.data.months || []);
        setSelectedMonth("all");
        setSelectedProduct(null);
        // Backend clears expenses on sales re-upload — mirror that in UI
        setExpensesFile(null);
        setResults(null);
      } catch (err) {
        setError(err.response?.data?.error || "Error al cargar ventas");
      } finally {
        setLoading(false);
      }
    },
    [calculate],
  );

  const onExpensesDrop = useCallback(
    async (files) => {
      const file = files[0];
      if (!file) return;
      setLoading(true);
      setError(null);
      const fd = new FormData();
      fd.append("file", file);
      try {
        await axios.post("/api/upload-expenses/", fd, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setExpensesFile(file.name);
        if (salesFile) calculate(selectedMonth, selectedProduct);
      } catch (err) {
        if (err.response?.data?.error === "date_mismatch") {
          const { sales_months, expense_months } = err.response.data;
          const fmt = (ms) => ms.map(fmtMonth).join(", ");
          setToast({
            open: true,
            message: `El archivo de gastos (${fmt(expense_months)}) no corresponde al período de ventas (${fmt(sales_months)}). Carga el archivo correcto.`,
          });
        } else {
          setError(err.response?.data?.error || "Error al cargar gastos");
        }
      } finally {
        setLoading(false);
      }
    },
    [salesFile, selectedMonth, selectedProduct, calculate],
  );

  // ── Month / Product ────────────────────────────────────────────────────────
  const handleMonthChange = (_, val) => {
    if (!val) return;
    setSelectedMonth(val);
    setSelectedProduct(null);
    setResults(null);
    calculate(val, null);
  };

  const handleProductChange = (_, val) => {
    setSelectedProduct(val);
    calculate(selectedMonth, val);
  };

  // ── Table modals ───────────────────────────────────────────────────────────
  const openSalesTable = async () => {
    try {
      const params =
        selectedMonth && selectedMonth !== "all"
          ? `?month=${selectedMonth}`
          : "";
      const res = await axios.get(`/api/data/sales/${params}`);
      setSalesTableData(res.data);
      setSalesTableOpen(true);
    } catch (err) {
      setError("Error al cargar tabla de ventas");
    }
  };

  const openExpensesTable = async () => {
    try {
      const params =
        selectedMonth && selectedMonth !== "all"
          ? `?month=${selectedMonth}`
          : "";
      const res = await axios.get(`/api/data/expenses/${params}`);
      setExpensesTableData(res.data);
      setExpensesTableOpen(true);
    } catch (err) {
      setError("Error al cargar tabla de gastos");
    }
  };

  const openPricesTable = async () => {
    try {
      const params =
        selectedMonth && selectedMonth !== "all"
          ? `?month=${selectedMonth}`
          : "";
      const res = await axios.get(`/api/data/product-prices/${params}`);
      setPricesTableData(res.data);
      setPricesTableOpen(true);
    } catch (err) {
      setError("Error al cargar tabla de precios");
    }
  };

  // ── Reset ──────────────────────────────────────────────────────────────────
  const handleReset = async () => {
    try {
      await axios.post("/api/reset/");
    } catch (_) {}
    setSalesFile(null);
    setExpensesFile(null);
    setMonths([]);
    setProducts([]);
    setSelectedMonth("all");
    setSelectedProduct(null);
    setResults(null);
    setError(null);
    setToast({ open: false, message: "" });
  };

  const sim = results?.simulation;
  const ing = results?.ingresos;
  const gas = results?.gastos;
  const ebt = results?.ebitda;
  const isCurrentMonth =
    months.includes(CURRENT_MONTH) &&
    (selectedMonth === CURRENT_MONTH ||
      (selectedMonth === "all" && months.length === 1));

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />

      {/* ── AppBar ── */}
      <AppNavBar
        bothUploaded={bothUploaded}
        hasAnyFile={!!(salesFile || expensesFile)}
        pdfLoading={pdfLoading}
        onOpenSalesTable={openSalesTable}
        onOpenExpensesTable={openExpensesTable}
        onOpenPricesTable={openPricesTable}
        onDownloadPdf={handleDownloadPdf}
        onOpenHelp={() => setHelpOpen(true)}
        onStartTour={startTour}
        onReset={handleReset}
      />

      <Container maxWidth="lg" sx={{ py: 4 }}>
        {error && (
          <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* ── Upload ── */}
        <h2 style={{ marginBottom: "10px" }}>
          Carga de Archivos del Mes a Evaluar (Carga un Solo Mes)
        </h2>
        <Box
          sx={{
            display: "flex",
            gap: 2,
            mb: 3,
            width: "100%",
            flexWrap: "wrap",
          }}
        >
          <Box
            data-tour="sales-upload"
            sx={{ flex: "1 1 0", minWidth: 280, minHeight: 200 }}
          >
            <DropzoneCard
              onDrop={onSalesDrop}
              title="Archivo de Ventas"
              subtitle="FUDO → Adiciones (.xls / .xlsx)"
              uploaded={!!salesFile}
              fileName={salesFile}
            />
          </Box>
          <Box
            data-tour="expenses-upload"
            sx={{ flex: "1 1 0", minWidth: 280, minHeight: 200 }}
          >
            <DropzoneCard
              onDrop={onExpensesDrop}
              title="Archivo de Gastos"
              subtitle="FUDO → Gastos (.xlsx)"
              uploaded={!!expensesFile}
              fileName={expensesFile}
            />
          </Box>
        </Box>

        {loading && (
          <LinearProgress color="primary" sx={{ mb: 3, borderRadius: 1 }} />
        )}

        {/* ── Month selector ── */}
        {bothUploaded && months.length > 1 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Período
            </Typography>
            <ToggleButtonGroup
              value={selectedMonth}
              exclusive
              onChange={handleMonthChange}
              size="small"
            >
              <ToggleButton value="all">Todos</ToggleButton>
              {months.map((m) => (
                <ToggleButton key={m} value={m}>
                  {fmtMonth(m)}
                </ToggleButton>
              ))}
            </ToggleButtonGroup>
          </Box>
        )}

        {/* ── KPI Cards ── */}
        {results && (
          <Box
            sx={{
              display: "flex",
              flexWrap: "wrap",
              gap: 2,
              mb: 3,
              width: "100%",
            }}
          >
            {/* Ingresos — widest for readability */}
            <Box
              sx={{
                flex: "1 1 420px",
                minWidth: 0,
                "@media (max-width: 900px)": { flex: "1 1 100%" },
              }}
            >
              <Paper
                elevation={0}
                sx={{ p: 3, height: "100%", border: "1px solid #1E3A5F" }}
              >
                <Typography variant="subtitle2" sx={{ mb: 2 }}>
                  💰 Ingresos
                </Typography>
                <KpiRow
                  label="Total bruto (c/IVA)"
                  value={CLP(ing.total_ingreso)}
                />
                <KpiRow
                  label="Total sin IVA"
                  value={CLP(ing.total_ingreso_sin_iva)}
                />
                <KpiRow label="COGS sin IVA" value={CLP(ing.costo_sin_iva)} />
                <KpiRow
                  label="Comisiones Uber Eats"
                  value={CLP(ing.comision_total)}
                  highlight="neg"
                  tooltip="30% del ingreso de pedidos Uber Eats"
                />
                <KpiRow
                  label="Margen bruto sin IVA"
                  value={CLP(ing.total_margen_sin_iva)}
                  highlight="pos"
                />
                <Divider sx={{ my: 1.5 }} />
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <Box>
                    <Typography variant="subtitle2" sx={{ mb: 0.3 }}>
                      CMV
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Costo de Mercadería Vendida · Meta: 25–35%
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: "right" }}>
                    <Chip
                      label={`${ing.cmv_percentage}%`}
                      color={cmvColor(ing.cmv_percentage)}
                      size="small"
                      sx={{
                        fontWeight: 700,
                        fontSize: "0.8rem",
                        height: 26,
                        mb: 0.5,
                      }}
                    />
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ display: "block" }}
                    >
                      {CLP(ing.cmv)}
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Box>

            {/* Gastos Operacionales — wider for readability */}
            <Box
              sx={{
                flex: "1 1 320px",
                minWidth: 0,
                "@media (max-width: 900px)": { flex: "1 1 100%" },
              }}
            >
              <Paper
                elevation={0}
                sx={{ p: 3, height: "100%", border: "1px solid #1E3A5F" }}
              >
                <Typography variant="subtitle2" sx={{ mb: 2 }}>
                  💸 Gastos Operacionales
                </Typography>
                <KpiRow
                  label="Total operacional"
                  value={CLP(gas.gastos_totales)}
                  highlight="neg"
                />
                <KpiRow label="Pagado" value={CLP(gas.pagados_totales)} />
                <KpiRow
                  label="Por pagar"
                  value={CLP(gas.por_pagar_totales)}
                  highlight={gas.por_pagar_totales > 0 ? "neg" : undefined}
                />
                <Divider sx={{ my: 1.5 }} />
                <Typography variant="subtitle2" sx={{ mb: 1, opacity: 0.5 }}>
                  Excluidos del EBITDA
                </Typography>
                <KpiRow
                  label="Préstamos socios"
                  value={CLP(gas.prestamos_socios)}
                  dimmed
                  tooltip="Actividad de financiamiento — no afecta el EBITDA operacional"
                />
                <KpiRow
                  label="Activo fijo (capex)"
                  value={CLP(gas.activo_fijo)}
                  dimmed
                  tooltip="Inversión en activos fijos — excluida del EBITDA"
                />
              </Paper>
            </Box>

            {/* EBITDA — compact, fixed width */}
            <Box
              sx={{
                flex: "0 0 280px",
                minWidth: 0,
                "@media (max-width: 900px)": { flex: "1 1 100%" },
              }}
            >
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  height: "100%",
                  border: "1px solid",
                  borderColor: ebt.ebitda >= 0 ? "#1E3A5F" : "#7F1D1D",
                }}
              >
                <Typography variant="subtitle2" sx={{ mb: 2 }}>
                  📈 EBITDA
                </Typography>
                <Box sx={{ textAlign: "center", py: 1.5 }}>
                  <Typography
                    variant="h2"
                    fontWeight={700}
                    sx={{
                      color:
                        ebt.ebitda_percentage >= 25
                          ? "success.main"
                          : ebt.ebitda_percentage >= 0
                            ? "warning.main"
                            : "error.main",
                    }}
                  >
                    {ebt.ebitda_percentage > 0 ? "+" : ""}
                    {ebt.ebitda_percentage}%
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mt: 0.5 }}
                  >
                    {CLP(ebt.ebitda)}
                  </Typography>
                </Box>
                <EbitdaGauge pct={ebt.ebitda_percentage} />
                <Box sx={{ mt: 2, textAlign: "center" }}>
                  <Chip
                    size="small"
                    label={
                      ebt.ebitda_percentage >= 25
                        ? "✓ Meta 25% alcanzada"
                        : `Faltan ${(25 - ebt.ebitda_percentage).toFixed(1)}pp para la meta`
                    }
                    color={ebt.ebitda_percentage >= 25 ? "success" : "default"}
                    sx={{ fontWeight: 500 }}
                  />
                </Box>
              </Paper>
            </Box>
          </Box>
        )}

        {/* ── Simulator ── */}
        {bothUploaded && products.length > 0 && !isCurrentMonth && (
          <Paper elevation={0} sx={{ p: 3, border: "1px solid #1E293B" }}>
            <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
              🎯{" "}
              {selectedMonth !== "all" && selectedMonth !== CURRENT_MONTH
                ? "Análisis Retrospectivo"
                : "Simulador"}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
              {selectedMonth !== "all" && selectedMonth !== CURRENT_MONTH
                ? "Selecciona un producto para ver cuántas unidades adicionales habrías necesitado vender para alcanzar el equilibrio o una rentabilidad del 25%."
                : "Selecciona un producto para calcular cuántas unidades adicionales necesitas vender para alcanzar el equilibrio o una rentabilidad del 25%."}
            </Typography>
            <Autocomplete
              options={products}
              value={selectedProduct}
              onChange={handleProductChange}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Buscar producto"
                  size="small"
                  sx={{ "& .MuiOutlinedInput-root": { bgcolor: "#0F172A" } }}
                />
              )}
              sx={{ maxWidth: 480, mb: sim ? 3 : 0 }}
            />

            {sim && (
              <>
                <Box
                  sx={{ display: "flex", gap: 1.5, mb: 2.5, flexWrap: "wrap" }}
                >
                  <Chip
                    size="small"
                    label={`Precio promedio s/IVA: ${CLP(sim.avg_ingreso_sin_iva_per_unit)}`}
                    variant="outlined"
                  />
                  <Chip
                    size="small"
                    label={`Margen s/IVA por unidad: ${CLP(sim.avg_margen_sin_iva_per_unit)} (${sim.margen_pct}%)`}
                    color={sim.margen_pct >= 25 ? "success" : "warning"}
                    variant="outlined"
                  />
                </Box>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <SimCard
                      icon={<BalanceIcon sx={{ color: "warning.main" }} />}
                      title="Punto de Equilibrio"
                      units={sim.breakeven_units}
                      alreadyMet={sim.already_breakeven}
                      impossible={sim.breakeven_units === null}
                      product={sim.producto}
                      extraRevenue={
                        sim.breakeven_units != null && !sim.already_breakeven
                          ? sim.breakeven_units *
                            sim.avg_ingreso_sin_iva_per_unit
                          : null
                      }
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <SimCard
                      icon={<TrendingUpIcon sx={{ color: "primary.main" }} />}
                      title="Meta EBITDA 25%"
                      units={sim.target_25_units}
                      alreadyMet={sim.already_25pct}
                      impossible={sim.target_25_units === null}
                      product={sim.producto}
                      extraRevenue={
                        sim.target_25_units != null && !sim.already_25pct
                          ? sim.target_25_units *
                            sim.avg_ingreso_sin_iva_per_unit
                          : null
                      }
                    />
                  </Grid>
                </Grid>
              </>
            )}
          </Paper>
        )}

        {/* ── Empty state ── */}
        {!salesFile && !expensesFile && (
          <Box sx={{ textAlign: "center", py: 10, color: "text.secondary" }}>
            <LocalPizzaIcon sx={{ fontSize: 56, opacity: 0.15, mb: 2 }} />
            <Typography variant="h6" sx={{ opacity: 0.35, fontWeight: 400 }}>
              Carga tus archivos de ventas y gastos para comenzar
            </Typography>
            <Button
              startIcon={<HelpOutlineIcon />}
              onClick={() => setHelpOpen(true)}
              sx={{ mt: 2, color: "text.secondary" }}
              size="small"
            >
              Ver cómo funciona
            </Button>
          </Box>
        )}

        {/* ── Projection Simulator (current month only) ── */}
        <ProjectionSimulator
          salesLoaded={!!salesFile}
          expensesLoaded={!!expensesFile}
          selectedMonth={selectedMonth}
          isCurrentMonth={isCurrentMonth}
          products={products}
        />

        {/* ── Price & Cost Scenario Simulator ── */}
        <PriceCostSimulator
          salesLoaded={!!salesFile}
          expensesLoaded={!!expensesFile}
          selectedMonth={selectedMonth}
        />

        {/* ── Charts ── */}
        <ChartsSection
          salesLoaded={!!salesFile}
          selectedMonth={selectedMonth}
        />
      </Container>

      {/* ── Modals ── */}
      <HelpModal open={helpOpen} onClose={() => setHelpOpen(false)} />
      <SalesTableModal
        open={salesTableOpen}
        onClose={() => setSalesTableOpen(false)}
        data={salesTableData}
        month={selectedMonth}
      />
      <ExpensesTableModal
        open={expensesTableOpen}
        onClose={() => setExpensesTableOpen(false)}
        data={expensesTableData}
        month={selectedMonth}
      />
      <ProductPricesModal
        open={pricesTableOpen}
        onClose={() => setPricesTableOpen(false)}
        data={pricesTableData}
        month={selectedMonth}
      />

      {/* ── Toast ── */}
      <Snackbar
        open={toast.open}
        autoHideDuration={8000}
        onClose={() => setToast((t) => ({ ...t, open: false }))}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          severity="warning"
          variant="filled"
          onClose={() => setToast((t) => ({ ...t, open: false }))}
          sx={{ maxWidth: 520 }}
        >
          {toast.message}
        </Alert>
      </Snackbar>
    </ThemeProvider>
  );
}
