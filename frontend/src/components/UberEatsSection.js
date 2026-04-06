import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import {
  Box,
  Paper,
  Typography,
  Divider,
  CircularProgress,
  Alert,
  Chip,
  Grid,
  LinearProgress,
  Tooltip,
} from "@mui/material";
import DeliveryDiningIcon from "@mui/icons-material/DeliveryDining";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

import ChannelSplitChart from "../charts/ChannelSplitChart";
import ChannelByCategoryChart from "../charts/ChannelByCategoryChart";
import UberEatsMarginChart from "../charts/UberEatsMarginChart";

const CLP = (v) =>
  new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    minimumFractionDigits: 0,
  }).format(v);

const KpiBox = ({ label, value, sub, color }) => (
  <Paper
    elevation={0}
    sx={{
      p: 2,
      border: "1px solid #1E3A5F",
      flex: 1,
      minWidth: 120,
    }}
  >
    <Typography variant="caption" color="text.secondary">
      {label}
    </Typography>
    <Typography variant="h6" fontWeight={700} color={color ?? "text.primary"}>
      {value}
    </Typography>
    {sub && (
      <Typography variant="caption" color="text.secondary">
        {sub}
      </Typography>
    )}
  </Paper>
);

const ChartCard = ({ children }) => (
  <Paper
    elevation={0}
    sx={{ p: 3, border: "1px solid #1E3A5F", height: "100%" }}
  >
    {children}
  </Paper>
);

const BreakevenCard = ({ data }) => {
  if (!data.fixed_costs) return null;

  const {
    fixed_costs,
    breakeven_units_per_day,
    units_per_day,
    breakeven_units_total,
    coverage_pct,
  } = data;
  const isAbove = units_per_day >= breakeven_units_per_day;
  const progress = Math.min(coverage_pct, 100);

  return (
    <Paper elevation={0} sx={{ p: 3, border: "1px solid #1E3A5F" }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
        <Typography variant="subtitle1" fontWeight={700}>
          Punto de Equilibrio en Uber Eats
        </Typography>
        <Tooltip
          title={
            <Box
              sx={{
                whiteSpace: "pre-line",
                fontSize: "0.75rem",
                lineHeight: 1.6,
              }}
            >
              {`¿Cuántos productos/día necesitas vender en Uber Eats para cubrir los costos fijos?\n\nFórmula:\n  Punto equilibrio = Costos fijos / Contribución prom. por unidad\n  Contribución = Precio s/IVA − Costo ingredientes − Comisión Uber (${data.commission_rate_pct}%)\n\nLos costos fijos excluyen préstamos y activos fijos.`}
            </Box>
          }
          arrow
          placement="right"
          componentsProps={{
            tooltip: {
              sx: {
                maxWidth: 340,
                bgcolor: "#1E293B",
                border: "1px solid #334155",
              },
            },
          }}
        >
          <InfoOutlinedIcon
            fontSize="small"
            sx={{ color: "#64748B", cursor: "help" }}
          />
        </Tooltip>
      </Box>

      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, mb: 3 }}>
        <KpiBox
          label="Costos fijos del período"
          value={CLP(fixed_costs)}
          sub={`${data.days_in_period} días`}
        />
        <KpiBox
          label="Contribución promedio por unidad"
          value={CLP(data.avg_contribution_per_unit)}
          sub="Precio − Ingredientes − Comisión"
          color={data.avg_contribution_per_unit >= 0 ? "#22C55E" : "#EF4444"}
        />
        <KpiBox
          label="Punto de equilibrio"
          value={`${Math.ceil(breakeven_units_per_day)} uds./día`}
          sub={`${Math.ceil(breakeven_units_total).toLocaleString("es-CL")} uds. totales`}
        />
        <KpiBox
          label="Ventas actuales Uber Eats"
          value={`${units_per_day.toFixed(1)} uds./día`}
          sub={`${data.total_units.toLocaleString("es-CL")} uds. totales`}
          color={isAbove ? "#22C55E" : "#F97316"}
        />
      </Box>

      <Box sx={{ mb: 1 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
          <Typography variant="caption" color="text.secondary">
            Cobertura de costos fijos con ventas Uber Eats actuales
          </Typography>
          <Typography
            variant="caption"
            fontWeight={700}
            color={isAbove ? "#22C55E" : "#F97316"}
          >
            {coverage_pct.toFixed(1)}%
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={progress}
          sx={{
            height: 8,
            borderRadius: 4,
            bgcolor: "#1E293B",
            "& .MuiLinearProgress-bar": {
              bgcolor: isAbove ? "#22C55E" : "#F97316",
              borderRadius: 4,
            },
          }}
        />
        <Box sx={{ display: "flex", justifyContent: "space-between", mt: 0.5 }}>
          <Typography variant="caption" color="text.secondary">
            0
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Meta: {Math.ceil(breakeven_units_per_day)} uds./día
          </Typography>
        </Box>
      </Box>

      <Alert
        severity={isAbove ? "success" : "warning"}
        sx={{
          mt: 2,
          bgcolor: isAbove ? "#22C55E10" : "#F9731610",
          border: "none",
        }}
      >
        {isAbove
          ? `Las ventas en Uber Eats cubren el ${coverage_pct.toFixed(1)}% de los costos fijos. Vendiendo ${units_per_day.toFixed(1)} uds./día, superas el punto de equilibrio de ${Math.ceil(breakeven_units_per_day)} uds./día.`
          : `Para cubrir los costos fijos solo con Uber Eats necesitas ${Math.ceil(breakeven_units_per_day)} uds./día. Actualmente vendes ${units_per_day.toFixed(1)} uds./día (${coverage_pct.toFixed(1)}% de la meta).`}
      </Alert>
    </Paper>
  );
};

const UberEatsSection = ({ salesLoaded, selectedMonth, chartData }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params =
        selectedMonth && selectedMonth !== "all"
          ? `?month=${selectedMonth}`
          : "";
      const res = await axios.get(`/api/uber-eats/analysis/${params}`);
      setData(res.data);
    } catch (err) {
      setError(
        err.response?.data?.error || "Error al cargar análisis Uber Eats",
      );
    } finally {
      setLoading(false);
    }
  }, [selectedMonth]);

  useEffect(() => {
    if (salesLoaded) fetchAnalysis();
  }, [salesLoaded, fetchAnalysis]);

  if (!salesLoaded) return null;

  return (
    <Box sx={{ mt: 4 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 3 }}>
        <DeliveryDiningIcon sx={{ color: "#3B82F6" }} />
        <Typography variant="h6" fontWeight={700}>
          Análisis Uber Eats
        </Typography>
        {data?.commission_rate_pct && (
          <Chip
            label={`Comisión ${data.commission_rate_pct}%`}
            size="small"
            sx={{ bgcolor: "#3B82F620", color: "#3B82F6", fontWeight: 600 }}
          />
        )}
        <Divider sx={{ flexGrow: 1, ml: 1 }} />
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress color="primary" />
        </Box>
      )}

      {!loading && data && !data.has_uber_data && (
        <Alert severity="info">
          No hay ventas registradas en Uber Eats para el período seleccionado.
        </Alert>
      )}

      {!loading && data && data.has_uber_data && (
        <>
          {/* ── KPI summary strip ── */}
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, mb: 3 }}>
            <KpiBox
              label="Unidades vendidas"
              value={data.total_units.toLocaleString("es-CL")}
              sub={`${data.units_per_day.toFixed(1)} uds./día · ${data.date_from} – ${data.date_to}`}
            />
            <KpiBox
              label="Ingreso s/IVA"
              value={CLP(data.total_revenue_sin_iva)}
              sub={`Precio prom. ${CLP(data.avg_price_sin_iva)}/unidad`}
            />
            <KpiBox
              label="Comisión Uber Eats (s/IVA)"
              value={CLP(data.total_commission_sin_iva)}
              sub={`Prom. ${CLP(data.avg_commission_per_unit)}/unidad`}
              color="#F97316"
            />
            <KpiBox
              label="Margen neto s/IVA"
              value={CLP(data.total_margin_sin_iva)}
              sub={`${data.margin_pct.toFixed(1)}%`}
              color={data.margin_pct >= 0 ? "#22C55E" : "#EF4444"}
            />
          </Box>

          {/* ── Channel split + category charts ── */}
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 3, mb: 3 }}>
            {chartData?.channel_split && (
              <Box sx={{ flex: "1 1 calc(50% - 12px)", minWidth: 280 }}>
                <ChartCard>
                  <ChannelSplitChart channelSplit={chartData.channel_split} />
                </ChartCard>
              </Box>
            )}
            {chartData?.channel_by_category && (
              <Box sx={{ flex: "1 1 calc(50% - 12px)", minWidth: 280 }}>
                <ChartCard>
                  <ChannelByCategoryChart
                    channelByCategory={chartData.channel_by_category}
                  />
                </ChartCard>
              </Box>
            )}
            {chartData?.channel_by_category && (
              <Box sx={{ flex: "1 1 calc(50% - 12px)", minWidth: 280 }}>
                <ChartCard>
                  <ChannelByCategoryChart
                    channelByCategory={chartData.channel_by_category}
                    showRevenue
                  />
                </ChartCard>
              </Box>
            )}
            <Box sx={{ flex: "1 1 calc(50% - 12px)", minWidth: 280 }}>
              <ChartCard>
                <UberEatsMarginChart
                  products={data.products}
                  height={Math.max(280, data.products.length * 28)}
                />
              </ChartCard>
            </Box>
          </Box>

          {/* ── Break-even ── */}
          <BreakevenCard data={data} />
        </>
      )}
    </Box>
  );
};

export default UberEatsSection;
