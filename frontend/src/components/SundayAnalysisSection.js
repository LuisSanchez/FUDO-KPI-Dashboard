import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import {
  Box,
  Paper,
  Typography,
  Divider,
  CircularProgress,
  Alert,
  LinearProgress,
  Tooltip,
} from "@mui/material";
import WeekendIcon from "@mui/icons-material/Weekend";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { Bar } from "react-chartjs-2";
import { useChartConfig, COLORS } from "../charts/chartConfig";
import { CLP } from "../utils/formatters";

const KpiBox = ({ label, value, sub, color }) => (
  <Paper
    elevation={0}
    sx={{
      p: 2,
      border: "1px solid",
      borderColor: "divider",
      flex: 1,
      minWidth: 140,
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

const BUCKET_COLORS = {
  Arriendo: "#3B82F6",
  Electricidad: "#F59E0B",
  Personal: "#8B5CF6",
  GGCC: "#10B981",
};

const WeekdayBarChart = ({ labels, values, neededRevenue }) => {
  const { baseOptions: bOpts } = useChartConfig();

  const bgColors = values.map((v, i) => {
    if (i === 6) return v > 0 ? "#22C55E80" : "#94A3B840";
    return COLORS.orangeFade;
  });
  const borderColors = values.map((v, i) => {
    if (i === 6) return v > 0 ? "#22C55E" : "#94A3B8";
    return COLORS.orange;
  });

  const datasets = [
    {
      type: "bar",
      label: "Ingreso promedio s/IVA",
      data: values,
      backgroundColor: bgColors,
      borderColor: borderColors,
      borderWidth: 1.5,
      borderRadius: 4,
      order: 2,
    },
  ];

  if (neededRevenue) {
    datasets.push({
      type: "line",
      label: "Ingreso mínimo requerido",
      data: labels.map(() => neededRevenue),
      borderColor: "#EF4444",
      borderWidth: 2,
      borderDash: [6, 3],
      pointRadius: 0,
      fill: false,
      order: 1,
    });
  }

  const data = { labels, datasets };

  const options = {
    ...bOpts,
    plugins: {
      ...bOpts.plugins,
      legend: {
        display: !!neededRevenue,
        labels: { ...bOpts.plugins?.legend?.labels, boxWidth: 20 },
      },
      tooltip: {
        ...bOpts.plugins.tooltip,
        callbacks: {
          label: ({ dataset, raw }) => ` ${dataset.label}: ${CLP(raw)}`,
        },
      },
    },
    scales: {
      ...bOpts.scales,
      y: {
        ...bOpts.scales.y,
        beginAtZero: true,
        ticks: {
          ...bOpts.scales.y.ticks,
          callback: (v) => `$${(v / 1_000_000).toFixed(1)}M`,
        },
      },
    },
  };

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
        Ingreso Promedio por Día de la Semana (s/IVA)
      </Typography>
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ display: "block", mb: 2 }}
      >
        Verde = Domingos · Línea roja = ingreso mínimo requerido
      </Typography>
      <Box sx={{ height: 240 }}>
        <Bar data={data} options={options} />
      </Box>
    </Box>
  );
};

const SundayAnalysisSection = ({
  salesLoaded,
  expensesLoaded,
  selectedMonth,
}) => {
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
      const res = await axios.get(`/api/sunday-analysis/${params}`);
      setData(res.data);
    } catch (err) {
      setError(
        err.response?.data?.error || "Error al cargar análisis dominical",
      );
    } finally {
      setLoading(false);
    }
  }, [selectedMonth]);

  useEffect(() => {
    if (salesLoaded) fetchAnalysis();
  }, [salesLoaded, expensesLoaded, fetchAnalysis]);

  if (!salesLoaded) return null;

  const sun = data?.sunday;
  const fc = data?.fixed_costs;

  const isViable = sun?.is_viable;
  const coverage = data?.coverage_pct ?? 0;
  const neededRevenue = data?.needed_revenue ?? 0;

  return (
    <Box sx={{ mt: 4 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 3 }}>
        <WeekendIcon sx={{ color: "#8B5CF6" }} />
        <Typography variant="h6" fontWeight={700}>
          ¿Conviene Abrir los Domingos?
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
              {`Analiza si el ingreso de los domingos cubre la parte proporcional de los costos fijos diarios.\n\nCostos incluidos: Arriendo, Electricidad, Personal y GGCC.\n\nFórmula:\n  Costo fijo diario = (Total costos) ÷ días del período\n  Ingreso mínimo = Costo fijo diario ÷ Margen contribución\n\nSi el ingreso promedio del domingo ≥ ingreso mínimo → viable.`}
            </Box>
          }
          arrow
          placement="right"
          componentsProps={{
            tooltip: {
              sx: {
                maxWidth: 340,
                bgcolor: "background.paper",
                color: "text.primary",
                border: "1px solid",
                borderColor: "divider",
              },
            },
            arrow: { sx: { color: "background.paper" } },
          }}
        >
          <InfoOutlinedIcon
            fontSize="small"
            sx={{ color: "text.secondary", cursor: "help" }}
          />
        </Tooltip>
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

      {!loading && data?.has_data && (
        <>
          {/* ── Fixed cost strip ── */}
          {data.has_expenses && fc && (
            <Paper
              elevation={0}
              sx={{ p: 3, border: "1px solid", borderColor: "divider", mb: 3 }}
            >
              <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 2 }}>
                Costos Fijos del Período (Arriendo + Electricidad + Personal +
                GGCC)
              </Typography>
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, mb: 3 }}>
                <KpiBox
                  label="Total del período"
                  value={CLP(fc.total)}
                  sub={`${data.days_in_period} días · ${data.date_from} – ${data.date_to}`}
                />
                <KpiBox
                  label="Costo fijo diario"
                  value={CLP(fc.daily)}
                  sub="Promedio por día"
                  color="#F97316"
                />
                <KpiBox
                  label="Ingreso mínimo por día"
                  value={CLP(neededRevenue)}
                  sub={`Margen contribución ${data.margin_rate_pct}%`}
                  color="#EF4444"
                />
              </Box>

              {/* Breakdown by bucket */}
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1.5 }}>
                {fc.breakdown.map((b) => (
                  <Paper
                    key={b.label}
                    elevation={0}
                    sx={{
                      px: 2,
                      py: 1,
                      border: "1px solid",
                      borderColor: "divider",
                      borderLeft: "3px solid",
                      borderLeftColor: BUCKET_COLORS[b.label] ?? "#94A3B8",
                    }}
                  >
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      display="block"
                    >
                      {b.label}
                    </Typography>
                    <Typography variant="body2" fontWeight={700}>
                      {CLP(b.total)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {CLP(Math.round(b.total / data.days_in_period))}/día
                    </Typography>
                  </Paper>
                ))}
              </Box>
            </Paper>
          )}

          {/* ── Weekday bar chart ── */}
          <Paper
            elevation={0}
            sx={{ p: 3, border: "1px solid", borderColor: "divider", mb: 3 }}
          >
            <WeekdayBarChart
              labels={data.weekday_avg_revenue.labels}
              values={data.weekday_avg_revenue.values}
              neededRevenue={data.has_expenses ? neededRevenue : null}
            />
          </Paper>

          {/* ── Sunday summary ── */}
          <Paper
            elevation={0}
            sx={{ p: 3, border: "1px solid", borderColor: "divider" }}
          >
            <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 2 }}>
              Desempeño Domingos
            </Typography>

            {!data.has_sunday_data ? (
              <Alert severity="info">
                No hay ventas registradas en domingos para el período
                seleccionado.
                {data.has_expenses && (
                  <>
                    {" "}
                    Para cubrir el costo fijo diario necesitarías al menos{" "}
                    <strong>{CLP(neededRevenue)}</strong> de ingreso s/IVA.
                  </>
                )}
              </Alert>
            ) : (
              <>
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, mb: 3 }}>
                  <KpiBox
                    label="Domingos en el período"
                    value={sun.num_sundays}
                    sub={`${sun.total_tickets} tickets totales`}
                  />
                  <KpiBox
                    label="Ingreso promedio domingo"
                    value={CLP(sun.avg_revenue)}
                    sub={`${sun.avg_tickets.toFixed(1)} tickets/domingo`}
                    color={
                      data.has_expenses
                        ? sun.avg_revenue >= neededRevenue
                          ? "#22C55E"
                          : "#EF4444"
                        : undefined
                    }
                  />
                  <KpiBox
                    label="Contribución promedio"
                    value={CLP(sun.avg_contribution)}
                    sub={`Margen ${data.margin_rate_pct}%`}
                    color={
                      data.has_expenses
                        ? sun.avg_contribution >= (fc?.daily ?? 0)
                          ? "#22C55E"
                          : "#F97316"
                        : undefined
                    }
                  />
                  {data.has_expenses && (
                    <KpiBox
                      label="Costo fijo diario"
                      value={CLP(fc.daily)}
                      sub="Arriendo + Elec + Personal + GGCC"
                      color="#F97316"
                    />
                  )}
                </Box>

                {data.has_expenses && (
                  <>
                    <Box sx={{ mb: 1 }}>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mb: 0.5,
                        }}
                      >
                        <Typography variant="caption" color="text.secondary">
                          Cobertura del costo fijo diario con ingreso dominical
                          promedio
                        </Typography>
                        <Typography
                          variant="caption"
                          fontWeight={700}
                          color={coverage >= 100 ? "#22C55E" : "#EF4444"}
                        >
                          {coverage.toFixed(1)}%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={Math.min(coverage, 100)}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          bgcolor: "action.hover",
                          "& .MuiLinearProgress-bar": {
                            bgcolor: coverage >= 100 ? "#22C55E" : "#EF4444",
                            borderRadius: 4,
                          },
                        }}
                      />
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mt: 0.5,
                        }}
                      >
                        <Typography variant="caption" color="text.secondary">
                          0
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Meta: {CLP(neededRevenue)}
                        </Typography>
                      </Box>
                    </Box>

                    <Alert
                      severity={isViable ? "success" : "warning"}
                      sx={{
                        mt: 2,
                        bgcolor: isViable ? "#22C55E10" : "#EF444410",
                        border: "none",
                      }}
                    >
                      {isViable
                        ? `Los domingos son viables: la contribución promedio (${CLP(sun.avg_contribution)}) supera el costo fijo diario (${CLP(fc.daily)}). Cubrís el ${coverage.toFixed(1)}% del mínimo requerido en ingresos.`
                        : `Los domingos no cubren su costo: necesitás ${CLP(neededRevenue)} de ingreso s/IVA pero el promedio es ${CLP(sun.avg_revenue)} (${coverage.toFixed(1)}% de la meta). Faltan ${CLP(neededRevenue - sun.avg_revenue)}.`}
                    </Alert>
                  </>
                )}
              </>
            )}
          </Paper>
        </>
      )}
    </Box>
  );
};

export default SundayAnalysisSection;
