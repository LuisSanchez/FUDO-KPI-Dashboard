import React, { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import {
  Box,
  Paper,
  Typography,
  Slider,
  TextField,
  InputAdornment,
  Divider,
  CircularProgress,
  Alert,
  Chip,
} from "@mui/material";
import PriceChangeIcon from "@mui/icons-material/PriceChange";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import TrendingDownIcon from "@mui/icons-material/TrendingDown";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

// ── Helpers ───────────────────────────────────────────────────────────────────
const CLP = (v) =>
  new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    minimumFractionDigits: 0,
  }).format(Math.round(v));

const ebitdaColor = (pct) =>
  pct >= 25 ? "#22C55E" : pct >= 0 ? "#FBBF24" : "#EF4444";

const sign = (v) => (v > 0 ? "+" : "");

// ── CompareRow ────────────────────────────────────────────────────────────────
const CompareRow = ({ label, current, projected, formatter, highlight }) => {
  const delta = projected - current;
  const deltaColor = delta > 0 ? "#22C55E" : delta < 0 ? "#EF4444" : "#64748B";

  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr 1fr 80px",
        gap: 1,
        py: 0.75,
        px: 1,
        borderRadius: 1,
        bgcolor: highlight ? "#0F172A" : "transparent",
        alignItems: "center",
      }}
    >
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography
        variant="caption"
        sx={{ textAlign: "right", color: "text.primary" }}
      >
        {formatter(current)}
      </Typography>
      <Typography
        variant="caption"
        sx={{
          textAlign: "right",
          color: highlight ? ebitdaColor(projected) : "text.primary",
          fontWeight: highlight ? 700 : 400,
        }}
      >
        {formatter(projected)}
      </Typography>
      <Typography
        variant="caption"
        sx={{ textAlign: "right", color: deltaColor, fontWeight: 600 }}
      >
        {delta !== 0 ? `${sign(delta)}${formatter(delta)}` : "—"}
      </Typography>
    </Box>
  );
};

// ── SliderInput ───────────────────────────────────────────────────────────────
const SliderInput = ({
  label,
  value,
  onChange,
  min,
  max,
  step,
  unit,
  marks,
}) => (
  <Box>
    <Box
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        mb: 0.5,
      }}
    >
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <TextField
        type="number"
        size="small"
        value={value}
        onChange={(e) => {
          const v = parseFloat(e.target.value);
          if (!isNaN(v)) onChange(Math.min(max, Math.max(min, v)));
        }}
        inputProps={{ min, max, step }}
        InputProps={{
          endAdornment: <InputAdornment position="end">{unit}</InputAdornment>,
        }}
        sx={{
          width: 120,
          "& .MuiOutlinedInput-root": { bgcolor: "#0F172A" },
          "& input": { textAlign: "right", fontSize: "0.8rem" },
        }}
      />
    </Box>
    <Slider
      value={value}
      onChange={(_, v) => onChange(v)}
      min={min}
      max={max}
      step={step}
      marks={marks}
      size="small"
      sx={{
        color: "primary.main",
        "& .MuiSlider-markLabel": { fontSize: "0.65rem", color: "#64748B" },
      }}
    />
  </Box>
);

// ── Main component ────────────────────────────────────────────────────────────
const PriceCostSimulator = ({ salesLoaded, expensesLoaded, selectedMonth }) => {
  const [priceIncrease, setPriceIncrease] = useState(0);
  const [costIncrease, setCostIncrease] = useState(0);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const debounceRef = useRef(null);

  const fetchSimulation = useCallback(
    async (price, cost) => {
      setLoading(true);
      setError(null);
      try {
        const params = { price_increase: price, cost_increase: cost };
        if (selectedMonth && selectedMonth !== "all")
          params.month = selectedMonth;
        const res = await axios.get("/api/simulate/price-cost/", { params });
        setData(res.data);
      } catch (err) {
        setError(err.response?.data?.error || "Error al calcular simulación");
      } finally {
        setLoading(false);
      }
    },
    [selectedMonth],
  );

  // Fetch baseline (0/0) when data is available or month changes
  useEffect(() => {
    if (salesLoaded && expensesLoaded) {
      fetchSimulation(0, 0);
    }
  }, [salesLoaded, expensesLoaded, selectedMonth, fetchSimulation]);

  // Debounce slider changes
  useEffect(() => {
    if (!salesLoaded || !expensesLoaded) return; // don't fetch without both files
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchSimulation(priceIncrease, costIncrease);
    }, 400);
    return () => clearTimeout(debounceRef.current);
  }, [priceIncrease, costIncrease]); // eslint-disable-line

  if (!salesLoaded) return null;

  if (!expensesLoaded) {
    return (
      <Paper elevation={0} sx={{ p: 3, border: "1px solid #1E293B", mt: 3 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
          <PriceChangeIcon sx={{ color: "primary.main" }} />
          <Typography variant="subtitle2">
            Simulador de Precio y Costos
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          Simula el impacto de subir el precio de venta y/o un alza en costos de
          ingredientes sobre el EBITDA del período.
        </Typography>
        <Alert severity="info" icon={false}>
          Carga el archivo de <strong>gastos</strong> para activar este
          simulador.
        </Alert>
      </Paper>
    );
  }

  const priceMarks = [
    { value: 0, label: "$0" },
    { value: 1000, label: "$1.000" },
    { value: 2500, label: "$2.500" },
    { value: 5000, label: "$5.000" },
  ];
  const costMarks = [
    { value: 0, label: "0%" },
    { value: 10, label: "10%" },
    { value: 25, label: "25%" },
    { value: 50, label: "50%" },
  ];

  const hasChanges = priceIncrease !== 0 || costIncrease !== 0;

  return (
    <Paper elevation={0} sx={{ p: 3, border: "1px solid #1E293B", mt: 3 }}>
      {/* Header */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
        <PriceChangeIcon sx={{ color: "primary.main" }} />
        <Typography variant="subtitle2">
          Simulador de Precio y Costos
        </Typography>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Simula el impacto de subir el precio de venta y/o un alza en el costo de
        ingredientes sobre el EBITDA del período seleccionado.
      </Typography>

      {/* Inputs */}
      <Box sx={{ display: "flex", gap: 4, flexWrap: "wrap", mb: 3 }}>
        <Box sx={{ flex: "1 1 260px", minWidth: 0 }}>
          <SliderInput
            label="Aumento de precio por Especialidad (con IVA)"
            value={priceIncrease}
            onChange={setPriceIncrease}
            min={0}
            max={5000}
            step={100}
            unit="$CLP"
            marks={priceMarks}
          />
        </Box>
        <Box sx={{ flex: "1 1 260px", minWidth: 0 }}>
          <SliderInput
            label="Alza en costo de ingredientes"
            value={costIncrease}
            onChange={setCostIncrease}
            min={0}
            max={50}
            step={1}
            unit="%"
            marks={costMarks}
          />
        </Box>
      </Box>

      {loading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 3 }}>
          <CircularProgress size={24} color="primary" />
        </Box>
      )}

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {data && !loading && (
        <>
          {/* Impact chips */}
          {hasChanges && (
            <Box sx={{ display: "flex", gap: 1.5, mb: 2.5, flexWrap: "wrap" }}>
              {priceIncrease > 0 && (
                <Chip
                  size="small"
                  icon={<TrendingUpIcon sx={{ fontSize: "14px !important" }} />}
                  label={`+${CLP(data.revenue_delta)} en ingresos s/IVA`}
                  sx={{ color: "#22C55E", borderColor: "#22C55E" }}
                  variant="outlined"
                />
              )}
              {costIncrease > 0 && (
                <Chip
                  size="small"
                  icon={
                    <TrendingDownIcon sx={{ fontSize: "14px !important" }} />
                  }
                  label={`+${CLP(data.cost_delta)} en CMV`}
                  sx={{ color: "#EF4444", borderColor: "#EF4444" }}
                  variant="outlined"
                />
              )}
              {hasChanges && (
                <Chip
                  size="small"
                  label={`Impacto neto: ${sign(data.net_delta)}${CLP(data.net_delta)}`}
                  sx={{
                    color: data.net_delta >= 0 ? "#22C55E" : "#EF4444",
                    borderColor: data.net_delta >= 0 ? "#22C55E" : "#EF4444",
                  }}
                  variant="outlined"
                />
              )}
            </Box>
          )}

          {/* EBITDA highlight */}
          <Box
            sx={{
              display: "flex",
              gap: 3,
              mb: 2.5,
              flexWrap: "wrap",
              alignItems: "center",
            }}
          >
            <Box>
              <Typography
                variant="caption"
                color="text.secondary"
                display="block"
              >
                EBITDA actual
              </Typography>
              <Typography
                variant="h4"
                fontWeight={700}
                sx={{
                  color: ebitdaColor(data.current_ebitda_pct),
                  lineHeight: 1.1,
                }}
              >
                {data.current_ebitda_pct}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {CLP(data.current_ebitda)}
              </Typography>
            </Box>

            {hasChanges && (
              <>
                <Typography variant="h5" color="text.secondary">
                  →
                </Typography>
                <Box>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    display="block"
                  >
                    EBITDA simulado
                  </Typography>
                  <Typography
                    variant="h4"
                    fontWeight={700}
                    sx={{
                      color: ebitdaColor(data.projected_ebitda_pct),
                      lineHeight: 1.1,
                    }}
                  >
                    {data.projected_ebitda_pct}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {CLP(data.projected_ebitda)}
                    {" · "}
                    <Box
                      component="span"
                      sx={{
                        color: data.net_delta >= 0 ? "#22C55E" : "#EF4444",
                        fontWeight: 600,
                      }}
                    >
                      {sign(
                        data.projected_ebitda_pct - data.current_ebitda_pct,
                      )}
                      {(
                        data.projected_ebitda_pct - data.current_ebitda_pct
                      ).toFixed(1)}{" "}
                      pp
                    </Box>
                  </Typography>
                </Box>
              </>
            )}
          </Box>

          <Divider sx={{ mb: 1.5 }} />

          {/* Comparison table */}
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr 80px",
              gap: 1,
              px: 1,
              mb: 0.5,
            }}
          >
            {["Métrica", "Actual", "Simulado", "Δ"].map((h) => (
              <Typography
                key={h}
                variant="caption"
                sx={{
                  color: "#475569",
                  fontWeight: 600,
                  textAlign: h !== "Métrica" ? "right" : "left",
                }}
              >
                {h}
              </Typography>
            ))}
          </Box>

          <CompareRow
            label="Ingreso s/IVA"
            current={data.current_ingreso_sin_iva}
            projected={data.projected_ingreso_sin_iva}
            formatter={CLP}
          />
          <CompareRow
            label="CMV ingredientes s/IVA"
            current={data.cmv_sin_iva_current}
            projected={data.cmv_sin_iva_projected}
            formatter={CLP}
          />
          <CompareRow
            label="EBITDA"
            current={data.current_ebitda}
            projected={data.projected_ebitda}
            formatter={CLP}
            highlight
          />
          <CompareRow
            label="EBITDA %"
            current={data.current_ebitda_pct}
            projected={data.projected_ebitda_pct}
            formatter={(v) => `${v.toFixed(1)}%`}
            highlight
          />
          <CompareRow
            label={`Precio prom. Especialidades (${(data.esp_units_sold ?? data.units_sold).toLocaleString("es-CL")} uds.)`}
            current={data.avg_price_clp_current}
            projected={data.avg_price_clp_projected}
            formatter={CLP}
          />

          <Divider sx={{ mt: 1.5, mb: 1.5 }} />

          {/* Disclaimer */}
          <Box sx={{ display: "flex", alignItems: "flex-start", gap: 1 }}>
            <InfoOutlinedIcon
              sx={{ fontSize: 14, color: "#475569", mt: 0.3, flexShrink: 0 }}
            />
            <Typography variant="caption" color="text.secondary">
              El aumento de precio aplica sobre todas las unidades del período
              (como si el precio nuevo hubiera estado vigente todo el mes). El
              alza de costos afecta únicamente el CMV de ingredientes; gastos
              fijos como arriendo, sueldos y servicios no se modifican. Los
              resultados son estimativos y no constituyen asesoría financiera.
            </Typography>
          </Box>
        </>
      )}
    </Paper>
  );
};

export default PriceCostSimulator;
