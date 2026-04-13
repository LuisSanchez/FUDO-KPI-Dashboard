import React, { useMemo, useState } from "react";
import { Bar } from "react-chartjs-2";
import {
  Box,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
} from "@mui/material";
import { useChartConfig, COLORS, CLP } from "./chartConfig";

/** Compute 7-day rolling average (trailing window). */
function rollingAvg(arr, window = 7) {
  return arr.map((_, i) => {
    const start = Math.max(0, i - window + 1);
    const slice = arr.slice(start, i + 1);
    return slice.reduce((s, v) => s + v, 0) / slice.length;
  });
}

const SalesTrend = ({ daily, height = 300 }) => {
  const [mode, setMode] = useState("revenue"); // "revenue" | "count"
  const { colors, baseOptions: bOpts } = useChartConfig();

  const arr = mode === "revenue" ? daily.revenue : daily.count;
  const avg7 = useMemo(() => rollingAvg(arr), [arr]);

  const data = useMemo(
    () => ({
      labels: daily.labels.map((d) => `Día ${d}`),
      datasets: [
        {
          type: "bar",
          label: mode === "revenue" ? "Ingreso diario s/IVA" : "Ventas diarias",
          data: arr,
          backgroundColor: COLORS.orangeFade,
          borderColor: COLORS.orange,
          borderWidth: 1.5,
          borderRadius: 4,
          order: 2,
        },
        {
          type: "line",
          label: "Promedio 7 días",
          data: avg7,
          borderColor: COLORS.blue,
          backgroundColor: "transparent",
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.4,
          order: 1,
        },
      ],
    }),
    [arr, avg7, daily.labels, mode],
  );

  const options = useMemo(
    () => ({
      ...bOpts,
      plugins: {
        ...bOpts.plugins,
        legend: {
          ...bOpts.plugins.legend,
          display: true,
          position: "top",
          align: "end",
        },
        tooltip: {
          ...bOpts.plugins.tooltip,
          mode: "index",
          intersect: false,
          callbacks: {
            title: ([item]) => item.label,
            label: ({ dataset, raw }) => {
              const val =
                mode === "revenue"
                  ? ` ${CLP(raw)}`
                  : ` ${Math.round(raw).toLocaleString("es-CL")} ventas`;
              return ` ${dataset.label}:${val}`;
            },
          },
        },
      },
      scales: {
        ...bOpts.scales,
        x: {
          ...bOpts.scales.x,
          ticks: { ...bOpts.scales.x.ticks, maxTicksLimit: 16 },
        },
        y: {
          ...bOpts.scales.y,
          beginAtZero: true,
          title: {
            display: true,
            text:
              mode === "revenue"
                ? "Ingreso sin IVA (CLP)"
                : "Cantidad de ventas",
            color: colors.text,
            font: { size: 11 },
          },
          ticks: {
            ...bOpts.scales.y.ticks,
            callback:
              mode === "revenue"
                ? (v) => `$${(v / 1_000_000).toFixed(1)}M`
                : undefined,
          },
        },
      },
    }),
    [mode, bOpts, colors],
  );

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between",
          mb: 2,
        }}
      >
        <Box>
          <Typography variant="subtitle2">Evolución Diaria del Mes</Typography>
          <Typography variant="caption" color="text.secondary">
            Barras: valor diario · Línea azul: promedio móvil 7 días
          </Typography>
        </Box>
        <ToggleButtonGroup
          value={mode}
          exclusive
          onChange={(_, v) => v && setMode(v)}
          size="small"
          sx={{ ml: 2 }}
        >
          <ToggleButton
            value="revenue"
            sx={{ px: 1.5, py: 0.25, fontSize: "0.7rem" }}
          >
            Ingresos
          </ToggleButton>
          <ToggleButton
            value="count"
            sx={{ px: 1.5, py: 0.25, fontSize: "0.7rem" }}
          >
            Ventas
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>
      <Box sx={{ height }}>
        <Bar data={data} options={options} />
      </Box>
    </Box>
  );
};

export default SalesTrend;
