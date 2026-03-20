import React, { useState, useCallback, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import axios from "axios";
import ChartsSection from "./charts/ChartsSection";
import ProjectionSimulator from "./components/ProjectionSimulator";
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
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
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import RefreshIcon from "@mui/icons-material/Refresh";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import BalanceIcon from "@mui/icons-material/Balance";
import LocalPizzaIcon from "@mui/icons-material/LocalPizza";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import TableChartIcon from "@mui/icons-material/TableChart";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import CloseIcon from "@mui/icons-material/Close";
import PriceCheckIcon from "@mui/icons-material/PriceCheck";

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

// ── Helpers ───────────────────────────────────────────────────────────────────
const CLP = (v) =>
  new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    minimumFractionDigits: 0,
  }).format(v);

const PCT = (v, decimals = 1) =>
  `${v > 0 ? "" : ""}${Number(v).toFixed(decimals)}%`;

const MONTH_NAMES = {
  "01": "Enero",
  "02": "Febrero",
  "03": "Marzo",
  "04": "Abril",
  "05": "Mayo",
  "06": "Junio",
  "07": "Julio",
  "08": "Agosto",
  "09": "Sep",
  10: "Oct",
  11: "Nov",
  12: "Dic",
};
const fmtMonth = (m) => {
  const [y, mo] = m.split("-");
  return `${MONTH_NAMES[mo]} ${y}`;
};

const cmvColor = (pct) =>
  pct <= 35 ? "success" : pct <= 42 ? "warning" : "error";

// ── Sub-components ─────────────────────────────────────────────────────────────

const KpiRow = ({ label, value, highlight, tooltip, dimmed }) => (
  <Box
    sx={{
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      py: 0.9,
      borderBottom: "1px solid",
      borderColor: "divider",
      opacity: dimmed ? 0.45 : 1,
    }}
  >
    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      {tooltip && (
        <Tooltip title={tooltip} arrow>
          <InfoOutlinedIcon
            sx={{ fontSize: 13, color: "#475569", cursor: "help" }}
          />
        </Tooltip>
      )}
    </Box>
    <Typography
      variant="body2"
      fontWeight={600}
      sx={{
        color:
          highlight === "pos"
            ? "success.main"
            : highlight === "neg"
              ? "error.main"
              : "text.primary",
      }}
    >
      {value}
    </Typography>
  </Box>
);

const DropzoneCard = ({ onDrop, title, subtitle, uploaded, fileName }) => {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
      "application/vnd.ms-excel": [".xls"],
    },
  });
  return (
    <Paper
      {...getRootProps()}
      elevation={0}
      sx={{
        p: 3,
        textAlign: "center",
        cursor: "pointer",
        transition: "all .2s",
        flex: 1,
        width: "100%",
        minHeight: 200,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        border: "2px dashed",
        borderColor: uploaded
          ? "success.main"
          : isDragActive
            ? "primary.main"
            : "#334155",
        bgcolor: uploaded
          ? "#22C55E10"
          : isDragActive
            ? "#F9731610"
            : "background.paper",
        "&:hover": {
          borderColor: uploaded ? "success.main" : "primary.main",
          transform: "translateY(-2px)",
          bgcolor: uploaded ? "#22C55E15" : "#F9731610",
        },
      }}
    >
      <input {...getInputProps()} />
      <Box sx={{ mb: 1.5 }}>
        {uploaded ? (
          <CheckCircleIcon sx={{ fontSize: 36, color: "success.main" }} />
        ) : (
          <UploadFileIcon
            sx={{
              fontSize: 36,
              color: isDragActive ? "primary.main" : "#475569",
            }}
          />
        )}
      </Box>
      <Typography variant="subtitle1" fontWeight={600} gutterBottom>
        {uploaded ? fileName : title}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {uploaded ? "Cargado · haz clic para reemplazar" : subtitle}
      </Typography>
    </Paper>
  );
};

const EbitdaGauge = ({ pct }) => {
  const clamp = Math.max(-200, Math.min(60, pct));
  const norm = ((clamp + 200) / 260) * 100;
  const zero = (200 / 260) * 100;
  const goal = ((200 + 25) / 260) * 100;
  return (
    <Box sx={{ mt: 2 }}>
      <Box
        sx={{
          position: "relative",
          height: 10,
          borderRadius: 5,
          bgcolor: "#0F172A",
          overflow: "hidden",
        }}
      >
        {pct >= 0 ? (
          <Box
            sx={{
              position: "absolute",
              left: `${zero}%`,
              top: 0,
              height: "100%",
              width: `${norm - zero}%`,
              bgcolor: pct >= 25 ? "#22C55E" : "#FBBF24",
              borderRadius: "0 5px 5px 0",
              transition: "width .6s ease",
            }}
          />
        ) : (
          <Box
            sx={{
              position: "absolute",
              left: `${norm}%`,
              top: 0,
              height: "100%",
              width: `${zero - norm}%`,
              bgcolor: "#EF4444",
              borderRadius: "5px 0 0 5px",
              transition: "width .6s ease",
            }}
          />
        )}
        <Box
          sx={{
            position: "absolute",
            left: `${zero}%`,
            top: 0,
            height: "100%",
            width: 2,
            bgcolor: "#475569",
          }}
        />
        <Box
          sx={{
            position: "absolute",
            left: `${goal}%`,
            top: 0,
            height: "100%",
            width: 2,
            bgcolor: "#F97316",
          }}
        />
      </Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", mt: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          Pérdida
        </Typography>
        <Typography variant="caption" color="text.secondary">
          0%
        </Typography>
        <Typography variant="caption" color="primary.main" fontWeight={600}>
          Meta 25%
        </Typography>
      </Box>
    </Box>
  );
};

const SimCard = ({
  icon,
  title,
  units,
  alreadyMet,
  impossible,
  product,
  extraRevenue,
}) => (
  <Paper
    elevation={0}
    sx={{
      p: 3,
      border: "1px solid",
      borderColor: alreadyMet
        ? "success.main"
        : impossible
          ? "#1E293B"
          : "divider",
      position: "relative",
      overflow: "hidden",
    }}
  >
    {alreadyMet && (
      <Box
        sx={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 3,
          bgcolor: "success.main",
          borderRadius: "12px 12px 0 0",
        }}
      />
    )}
    <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
      {icon}
      <Typography variant="subtitle2">{title}</Typography>
    </Box>
    {alreadyMet ? (
      <Typography variant="h6" color="success.main">
        ✓ Ya alcanzado
      </Typography>
    ) : impossible ? (
      <Box>
        <Typography variant="h6" color="text.secondary">
          No calculable
        </Typography>
        <Typography variant="caption" color="text.secondary">
          El margen de este producto es insuficiente para alcanzar la meta
        </Typography>
      </Box>
    ) : (
      <Box>
        <Typography variant="h3" fontWeight={700} color="primary.main">
          {units?.toLocaleString("es-CL")}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          unidades adicionales de{" "}
          <strong style={{ color: "#F1F5F9" }}>{product}</strong>
        </Typography>
        {extraRevenue != null && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ display: "block", mt: 1 }}
          >
            ≈ {CLP(extraRevenue)} en ingresos adicionales (sin IVA)
          </Typography>
        )}
      </Box>
    )}
  </Paper>
);

// ── Help Modal ────────────────────────────────────────────────────────────────
const HelpModal = ({ open, onClose }) => (
  <Dialog
    open={open}
    onClose={onClose}
    maxWidth="md"
    fullWidth
    PaperProps={{ sx: { bgcolor: "#1E293B", border: "1px solid #334155" } }}
  >
    <DialogTitle
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <HelpOutlineIcon color="primary" />
        <Typography variant="h6">Cómo funciona FUDO Analytics</Typography>
      </Box>
      <IconButton onClick={onClose} size="small">
        <CloseIcon fontSize="small" />
      </IconButton>
    </DialogTitle>
    <DialogContent dividers sx={{ borderColor: "#334155" }}>
      <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
        <Box>
          <Typography variant="subtitle2" color="primary.main" sx={{ mb: 1 }}>
            ¿Qué hace esta app?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Analiza la rentabilidad de tu tienda de pizza cargando los reportes
            de ventas y gastos exportados desde FUDO. Calcula automáticamente
            EBITDA, CMV, márgenes y simula cuántas unidades adicionales
            necesitas vender para alcanzar el equilibrio o una meta de
            rentabilidad del 25%.
          </Typography>
        </Box>

        <Box>
          <Typography variant="subtitle2" color="primary.main" sx={{ mb: 1 }}>
            Archivos necesarios (desde FUDO)
          </Typography>
          <Box component="ul" sx={{ pl: 2, m: 0 }}>
            {[
              [
                "Ventas",
                'Exportar reporte "Adiciones" (.xls). Contiene el detalle de cada ítem vendido con precio y costo de ingredientes.',
              ],
              [
                "Gastos",
                'Exportar reporte "Gastos" (.xlsx). Contiene todos los gastos registrados con proveedor, categoría e importe.',
              ],
            ].map(([t, d]) => (
              <Box component="li" key={t} sx={{ mb: 1 }}>
                <Typography variant="body2">
                  <strong style={{ color: "#F1F5F9" }}>{t}:</strong>{" "}
                  <span style={{ color: "#94A3B8" }}>{d}</span>
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>

        <Box>
          <Typography variant="subtitle2" color="primary.main" sx={{ mb: 1 }}>
            Cálculos y fórmulas
          </Typography>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
            {[
              [
                "IVA (19%)",
                'Los precios de venta de FUDO incluyen IVA, igual que los costos de ingredientes. Todos los valores "sin IVA" se obtienen dividiendo por 1.19, permitiendo comparar en términos netos. El IVA no es ingreso real — lo recaudas y lo devuelves al SII.',
              ],
              [
                "CMV — Costo de Mercadería Vendida",
                "CMV% = (Costo ingredientes sin IVA) / (Ingreso sin IVA) × 100. Mide qué fracción de cada peso de venta se destina a ingredientes y modificadores. Rango ideal para restaurantes: 25–35%. Por debajo del 25% es excelente; por encima del 42% indica problemas en costos o precios.",
              ],
              [
                "Comisión Uber Eats (30%)",
                'Los pedidos con origen "uber_eats" tienen un 30% del ingreso descontado como comisión de plataforma. Esta comisión se suma al costo total del ítem. El ingreso bruto que ves incluye la comisión; el margen ya la descuenta.',
              ],
              [
                "Margen bruto sin IVA",
                "Ingreso sin IVA − COGS sin IVA (ingredientes + modificadores + comisiones). Representa lo que queda de cada venta antes de pagar gastos fijos.",
              ],
              [
                "EBITDA",
                "EBITDA = Margen bruto sin IVA − Gastos operacionales. Los préstamos de socios y activos fijos (capex) se excluyen porque son actividades de financiamiento/inversión, no operacionales. El % se calcula sobre el ingreso sin IVA.",
              ],
              [
                "Simulador",
                "Para el producto seleccionado, calcula el promedio de margen por unidad vendida históricamente. Luego resuelve: ¿cuántas unidades adicionales se necesitan para que EBITDA = 0 (equilibrio) y para que EBITDA% = 25%? La fórmula es x = (0.25·I + G − M) / (m − 0.25·i), donde M = margen actual, G = gastos, I = ingreso, m e i = margen e ingreso por unidad.",
              ],
            ].map(([title, text]) => (
              <Box key={title}>
                <Typography
                  variant="body2"
                  fontWeight={600}
                  sx={{ color: "#F1F5F9", mb: 0.3 }}
                >
                  {title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {text}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>

        <Box
          sx={{
            bgcolor: "#F97316" + "15",
            border: "1px solid",
            borderColor: "#F97316" + "40",
            borderRadius: 2,
            p: 2,
          }}
        >
          <Typography
            variant="body2"
            sx={{ color: "#FBBF24", fontWeight: 600, mb: 0.5 }}
          >
            ⚠️ Los datos son efímeros
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Los archivos cargados se almacenan en memoria mientras el servidor
            está activo. Al reiniciar el servidor o hacer clic en "Reiniciar",
            todos los datos se pierden. No se guarda ninguna información en base
            de datos. En una versión futura se añadirá persistencia.
          </Typography>
        </Box>
      </Box>
    </DialogContent>
    <DialogActions sx={{ px: 3, py: 2 }}>
      <Button onClick={onClose} variant="contained" color="primary">
        Entendido
      </Button>
    </DialogActions>
  </Dialog>
);

// ── Sales Table Modal ─────────────────────────────────────────────────────────
const SalesTableModal = ({ open, onClose, data, month }) => {
  const [orderBy, setOrderBy] = useState("ingreso_sin_iva");
  const [order, setOrder] = useState("desc");

  const handleSort = (col) => {
    if (orderBy === col) setOrder((o) => (o === "asc" ? "desc" : "asc"));
    else {
      setOrderBy(col);
      setOrder("desc");
    }
  };

  const sorted = [...(data || [])].sort((a, b) =>
    order === "asc" ? a[orderBy] - b[orderBy] : b[orderBy] - a[orderBy],
  );

  const cols = [
    { id: "Producto", label: "Producto", numeric: false },
    { id: "Categoría", label: "Categoría", numeric: false },
    { id: "cantidad", label: "Cant.", numeric: true },
    { id: "ingreso_sin_iva", label: "Ingreso s/IVA", numeric: true },
    { id: "cmv_pct", label: "CMV%", numeric: true },
    { id: "cmv", label: "CMV $", numeric: true },
    { id: "margen_sin_iva", label: "Margen s/IVA", numeric: true },
    { id: "margen_pct", label: "Margen%", numeric: true },
    { id: "comision", label: "Comisión UE", numeric: true },
  ];

  const totals = sorted.reduce(
    (acc, r) => ({
      cantidad: acc.cantidad + r.cantidad,
      ingreso_sin_iva: acc.ingreso_sin_iva + r.ingreso_sin_iva,
      cmv: acc.cmv + r.cmv,
      margen_sin_iva: acc.margen_sin_iva + r.margen_sin_iva,
      comision: acc.comision + r.comision,
    }),
    { cantidad: 0, ingreso_sin_iva: 0, cmv: 0, margen_sin_iva: 0, comision: 0 },
  );
  const totalCmvPct =
    totals.ingreso_sin_iva > 0
      ? ((totals.cmv / totals.ingreso_sin_iva) * 100).toFixed(1)
      : "—";
  const totalMarPct =
    totals.ingreso_sin_iva > 0
      ? ((totals.margen_sin_iva / totals.ingreso_sin_iva) * 100).toFixed(1)
      : "—";

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xl"
      fullWidth
      PaperProps={{
        sx: {
          bgcolor: "#1E293B",
          border: "1px solid #334155",
          maxHeight: "90vh",
        },
      }}
    >
      <DialogTitle
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <TableChartIcon color="primary" />
          <Typography variant="h6">
            Ventas por Producto
            {month && month !== "all" ? ` — ${fmtMonth(month)}` : ""}
          </Typography>
          <Chip
            label={`${sorted.length} productos`}
            size="small"
            variant="outlined"
          />
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>
      <DialogContent sx={{ p: 0 }}>
        <TableContainer sx={{ maxHeight: "70vh" }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                {cols.map((c) => (
                  <TableCell key={c.id} align={c.numeric ? "right" : "left"}>
                    <TableSortLabel
                      active={orderBy === c.id}
                      direction={orderBy === c.id ? order : "desc"}
                      onClick={() => c.numeric && handleSort(c.id)}
                      hideSortIcon={!c.numeric}
                    >
                      {c.label}
                    </TableSortLabel>
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {sorted.map((row, i) => (
                <TableRow
                  key={i}
                  hover
                  sx={{ "&:hover": { bgcolor: "#ffffff08" } }}
                >
                  <TableCell sx={{ fontWeight: 500 }}>{row.Producto}</TableCell>
                  <TableCell>
                    <Chip
                      label={row.Categoría}
                      size="small"
                      sx={{ fontSize: "0.65rem", height: 18 }}
                    />
                  </TableCell>
                  <TableCell align="right">
                    {row.cantidad.toLocaleString("es-CL")}
                  </TableCell>
                  <TableCell align="right">
                    {CLP(row.ingreso_sin_iva)}
                  </TableCell>
                  <TableCell align="right">
                    <Chip
                      label={`${row.cmv_pct}%`}
                      size="small"
                      color={cmvColor(row.cmv_pct)}
                      sx={{ fontSize: "0.65rem", height: 20 }}
                    />
                  </TableCell>
                  <TableCell align="right">{CLP(row.cmv)}</TableCell>
                  <TableCell align="right">{CLP(row.margen_sin_iva)}</TableCell>
                  <TableCell align="right">
                    <Typography
                      variant="caption"
                      sx={{
                        color:
                          row.margen_pct >= 50
                            ? "success.main"
                            : row.margen_pct >= 30
                              ? "warning.main"
                              : "error.main",
                        fontWeight: 600,
                      }}
                    >
                      {row.margen_pct}%
                    </Typography>
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{
                      color: row.comision > 0 ? "error.main" : "text.secondary",
                    }}
                  >
                    {row.comision > 0 ? CLP(row.comision) : "—"}
                  </TableCell>
                </TableRow>
              ))}
              {/* Totals row */}
              <TableRow
                sx={{ bgcolor: "#0F172A", position: "sticky", bottom: 0 }}
              >
                <TableCell
                  colSpan={2}
                  sx={{ fontWeight: 700, color: "#F1F5F9" }}
                >
                  TOTAL
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  {totals.cantidad.toLocaleString("es-CL")}
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  {CLP(totals.ingreso_sin_iva)}
                </TableCell>
                <TableCell align="right">
                  <Chip
                    label={`${totalCmvPct}%`}
                    size="small"
                    color={cmvColor(parseFloat(totalCmvPct))}
                    sx={{ fontSize: "0.65rem", height: 20 }}
                  />
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  {CLP(totals.cmv)}
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  {CLP(totals.margen_sin_iva)}
                </TableCell>
                <TableCell
                  align="right"
                  sx={{ fontWeight: 700, color: "success.main" }}
                >
                  {totalMarPct}%
                </TableCell>
                <TableCell
                  align="right"
                  sx={{ fontWeight: 700, color: "error.main" }}
                >
                  {CLP(totals.comision)}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </DialogContent>
    </Dialog>
  );
};

// ── Expenses Table Modal ──────────────────────────────────────────────────────
const TIPO_COLOR = {
  Operacional: "default",
  Préstamo: "warning",
  "Activo Fijo": "info",
};

const ExpensesTableModal = ({ open, onClose, data, month }) => {
  const [filter, setFilter] = useState("all");

  const filtered = (data || []).filter(
    (r) => filter === "all" || r.Tipo === filter,
  );
  const total = filtered.reduce((s, r) => s + r.Importe, 0);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xl"
      fullWidth
      PaperProps={{
        sx: {
          bgcolor: "#1E293B",
          border: "1px solid #334155",
          maxHeight: "90vh",
        },
      }}
    >
      <DialogTitle
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <ReceiptLongIcon color="primary" />
          <Typography variant="h6">
            Gastos{month && month !== "all" ? ` — ${fmtMonth(month)}` : ""}
          </Typography>
          <Chip
            label={`${filtered.length} registros`}
            size="small"
            variant="outlined"
          />
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>
      <DialogContent sx={{ p: 0 }}>
        {/* Filter tabs */}
        <Box sx={{ px: 2, pt: 2, pb: 1, display: "flex", gap: 1 }}>
          {["all", "Operacional", "Préstamo", "Activo Fijo"].map((t) => (
            <Chip
              key={t}
              label={t === "all" ? "Todos" : t}
              size="small"
              onClick={() => setFilter(t)}
              variant={filter === t ? "filled" : "outlined"}
              color={filter === t ? "primary" : "default"}
              sx={{ cursor: "pointer" }}
            />
          ))}
          <Box sx={{ ml: "auto" }}>
            <Typography variant="body2" fontWeight={600}>
              Total: {CLP(total)}
            </Typography>
          </Box>
        </Box>
        <TableContainer sx={{ maxHeight: "65vh" }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                {[
                  "Fecha",
                  "Proveedor",
                  "Categoría",
                  "Subcategoría",
                  "Comentario",
                  "Importe",
                  "Estado",
                  "Tipo",
                ].map((h) => (
                  <TableCell key={h} align={h === "Importe" ? "right" : "left"}>
                    {h}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {filtered.map((row, i) => (
                <TableRow
                  key={i}
                  hover
                  sx={{ "&:hover": { bgcolor: "#ffffff08" } }}
                >
                  <TableCell
                    sx={{ whiteSpace: "nowrap", color: "text.secondary" }}
                  >
                    {row.Fecha}
                  </TableCell>
                  <TableCell sx={{ fontWeight: 500, maxWidth: 180 }}>
                    {row.Proveedor}
                  </TableCell>
                  <TableCell>{row.Categoría}</TableCell>
                  <TableCell
                    sx={{ color: "text.secondary", fontSize: "0.8rem" }}
                  >
                    {row.Subcategoría || "—"}
                  </TableCell>
                  <TableCell
                    sx={{
                      color: "text.secondary",
                      fontSize: "0.8rem",
                      maxWidth: 200,
                    }}
                  >
                    {row.Comentario || "—"}
                  </TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>
                    {CLP(row.Importe)}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={row["Estado del pago"]}
                      size="small"
                      color={
                        row["Estado del pago"] === "Pagado"
                          ? "success"
                          : "warning"
                      }
                      sx={{ fontSize: "0.65rem", height: 20 }}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={row.Tipo}
                      size="small"
                      color={TIPO_COLOR[row.Tipo] || "default"}
                      sx={{ fontSize: "0.65rem", height: 20 }}
                    />
                  </TableCell>
                </TableRow>
              ))}
              <TableRow
                sx={{ bgcolor: "#0F172A", position: "sticky", bottom: 0 }}
              >
                <TableCell colSpan={5} sx={{ fontWeight: 700 }}>
                  TOTAL
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  {CLP(total)}
                </TableCell>
                <TableCell colSpan={2} />
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </DialogContent>
    </Dialog>
  );
};

// ── Product Prices Table Modal ────────────────────────────────────────────────
const ProductPricesModal = ({ open, onClose, data, month }) => {
  const [orderBy, setOrderBy] = useState("avg_precio_neto");
  const [order, setOrder] = useState("desc");

  const handleSort = (col) => {
    if (orderBy === col) setOrder((o) => (o === "asc" ? "desc" : "asc"));
    else { setOrderBy(col); setOrder("desc"); }
  };

  const sorted = [...(data || [])].sort((a, b) => {
    const av = a[orderBy], bv = b[orderBy];
    if (typeof av === "string") return order === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
    return order === "asc" ? av - bv : bv - av;
  });

  const cols = [
    { id: "Producto",        label: "Producto",        numeric: false },
    { id: "Categoría",       label: "Categoría",       numeric: false },
    { id: "cantidad",        label: "Cant.",           numeric: true  },
    { id: "avg_precio",      label: "Precio (c/IVA)",  numeric: true  },
    { id: "avg_iva",         label: "IVA",             numeric: true  },
    { id: "avg_precio_neto", label: "Precio neto",     numeric: true  },
    { id: "avg_costo_neto",  label: "Costo neto",      numeric: true  },
    { id: "pct_costo",       label: "% Costo",         numeric: true  },
    { id: "margen_bruto",    label: "Margen bruto",    numeric: true  },
    { id: "pct_margen_bruto",label: "% Margen",        numeric: true  },
  ];

  const marginColor = (pct) =>
    pct >= 60 ? "success" : pct >= 40 ? "warning" : "error";

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xl"
      fullWidth
      PaperProps={{ sx: { bgcolor: "#1E293B", border: "1px solid #334155", maxHeight: "90vh" } }}
    >
      <DialogTitle sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <PriceCheckIcon color="primary" />
          <Typography variant="h6">
            Precios y Márgenes por Producto
            {month && month !== "all" ? ` — ${fmtMonth(month)}` : ""}
          </Typography>
          <Chip label={`${sorted.length} productos`} size="small" variant="outlined" />
        </Box>
        <IconButton onClick={onClose} size="small"><CloseIcon fontSize="small" /></IconButton>
      </DialogTitle>
      <DialogContent sx={{ p: 0 }}>
        <TableContainer sx={{ maxHeight: "70vh" }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                {cols.map((c) => (
                  <TableCell key={c.id} align={c.numeric ? "right" : "left"}>
                    <TableSortLabel
                      active={orderBy === c.id}
                      direction={orderBy === c.id ? order : "desc"}
                      onClick={() => handleSort(c.id)}
                      hideSortIcon={false}
                    >
                      {c.label}
                    </TableSortLabel>
                  </TableCell>
                ))}
                <TableCell>Canales</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sorted.map((row, i) => (
                <TableRow key={i} hover sx={{ "&:hover": { bgcolor: "#ffffff08" } }}>
                  <TableCell sx={{ fontWeight: 500 }}>{row.Producto}</TableCell>
                  <TableCell>
                    <Chip label={row.Categoría} size="small" sx={{ fontSize: "0.65rem", height: 18 }} />
                  </TableCell>
                  <TableCell align="right">{row.cantidad.toLocaleString("es-CL")}</TableCell>
                  <TableCell align="right">{CLP(row.avg_precio)}</TableCell>
                  <TableCell align="right" sx={{ color: "text.secondary" }}>{CLP(row.avg_iva)}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>{CLP(row.avg_precio_neto)}</TableCell>
                  <TableCell align="right" sx={{ color: "warning.main" }}>{CLP(row.avg_costo_neto)}</TableCell>
                  <TableCell align="right">
                    <Chip
                      label={`${row.pct_costo}%`}
                      size="small"
                      color={cmvColor(row.pct_costo)}
                      sx={{ fontSize: "0.65rem", height: 20 }}
                    />
                  </TableCell>
                  <TableCell align="right" sx={{ color: row.margen_bruto >= 0 ? "success.main" : "error.main", fontWeight: 600 }}>
                    {CLP(row.margen_bruto)}
                  </TableCell>
                  <TableCell align="right">
                    <Chip
                      label={`${row.pct_margen_bruto}%`}
                      size="small"
                      color={marginColor(row.pct_margen_bruto)}
                      sx={{ fontSize: "0.65rem", height: 20 }}
                    />
                  </TableCell>
                  <TableCell>
                    {row.tiene_uber_eats && (
                      <Chip label="Uber Eats" size="small" sx={{ fontSize: "0.6rem", height: 18, bgcolor: "#1C1C1C", color: "#06B6D4" }} />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </DialogContent>
    </Dialog>
  );
};

// ── Main App ──────────────────────────────────────────────────────────────────
const CURRENT_MONTH = new Date().toISOString().slice(0, 7); // e.g. "2026-03"

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
  const [toast, setToast] = useState({ open: false, message: '' });

  const bothUploaded = !!(salesFile && expensesFile);

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
    setToast({ open: false, message: '' });
  };

  const sim = results?.simulation;
  const ing = results?.ingresos;
  const gas = results?.gastos;
  const ebt = results?.ebitda;
  const isCurrentMonth =
    months.includes(CURRENT_MONTH) &&
    (selectedMonth === CURRENT_MONTH || (selectedMonth === "all" && months.length === 1));

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />

      {/* ── AppBar ── */}
      <AppBar
        position="static"
        elevation={0}
        sx={{ bgcolor: "#0F172A", borderBottom: "1px solid #1E293B" }}
      >
        <Toolbar
          sx={{
            maxWidth: 1200,
            mx: "auto",
            width: "100%",
            px: { xs: 2, md: 4 },
            gap: 1,
          }}
        >
          <LocalPizzaIcon sx={{ color: "primary.main", fontSize: 28 }} />
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" fontWeight={700} sx={{ lineHeight: 1.2 }}>
              FUDO Analytics
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Food Finance Dashboard
            </Typography>
          </Box>
          {bothUploaded && (
            <>
              <Tooltip title="Ver tabla de ventas">
                <Button
                  size="small"
                  startIcon={<TableChartIcon />}
                  onClick={openSalesTable}
                  sx={{
                    color: "text.secondary",
                    "&:hover": { color: "text.primary" },
                  }}
                >
                  Ventas
                </Button>
              </Tooltip>
              <Tooltip title="Ver tabla de gastos">
                <Button
                  size="small"
                  startIcon={<ReceiptLongIcon />}
                  onClick={openExpensesTable}
                  sx={{
                    color: "text.secondary",
                    "&:hover": { color: "text.primary" },
                  }}
                >
                  Gastos
                </Button>
              </Tooltip>
              <Tooltip title="Ver precios y márgenes por producto">
                <Button
                  size="small"
                  startIcon={<PriceCheckIcon />}
                  onClick={openPricesTable}
                  sx={{
                    color: "text.secondary",
                    "&:hover": { color: "text.primary" },
                  }}
                >
                  Precios
                </Button>
              </Tooltip>
            </>
          )}
          <Tooltip title="Cómo funciona">
            <IconButton
              onClick={() => setHelpOpen(true)}
              size="small"
              sx={{ color: "text.secondary" }}
            >
              <HelpOutlineIcon />
            </IconButton>
          </Tooltip>
          {(salesFile || expensesFile) && (
            <Tooltip title="Reiniciar datos">
              <IconButton
                onClick={handleReset}
                size="small"
                sx={{ color: "text.secondary" }}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          )}
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        {error && (
          <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* ── Upload ── */}
        <Box
          sx={{
            display: "flex",
            gap: 2,
            mb: 3,
            width: "100%",
            flexWrap: "wrap",
          }}
        >
          <Box sx={{ flex: "1 1 0", minWidth: 280, minHeight: 200 }}>
            <DropzoneCard
              onDrop={onSalesDrop}
              title="Archivo de Ventas"
              subtitle="FUDO → Adiciones (.xls / .xlsx)"
              uploaded={!!salesFile}
              fileName={salesFile}
            />
          </Box>
          <Box sx={{ flex: "1 1 0", minWidth: 280, minHeight: 200 }}>
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
              🎯 {selectedMonth !== 'all' && selectedMonth !== CURRENT_MONTH
                    ? 'Análisis Retrospectivo'
                    : 'Simulador'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
              {selectedMonth !== 'all' && selectedMonth !== CURRENT_MONTH
                ? 'Selecciona un producto para ver cuántas unidades adicionales habrías necesitado vender para alcanzar el equilibrio o una rentabilidad del 25%.'
                : 'Selecciona un producto para calcular cuántas unidades adicionales necesitas vender para alcanzar el equilibrio o una rentabilidad del 25%.'}
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
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
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
