import React, { useMemo } from "react";
import { Bar } from "react-chartjs-2";
import { Box, Typography } from "@mui/material";
import { baseOptions, COLORS, CLP } from "./chartConfig";

const SalesByWeekday = ({ weekday, height = 260, showRevenue = false }) => {
  const arr = showRevenue ? weekday.revenue : weekday.count;

  const bestIdx = useMemo(() => arr.indexOf(Math.max(...arr)), [arr]);

  const data = useMemo(
    () => ({
      labels: weekday.labels,
      datasets: [
        {
          label: showRevenue ? "Ingreso sin IVA" : "Ventas (líneas)",
          data: arr,
          backgroundColor: arr.map((_, i) =>
            i === bestIdx ? COLORS.orange : COLORS.orangeFade,
          ),
          borderColor: arr.map((_, i) =>
            i === bestIdx ? COLORS.orange : COLORS.orange + "80",
          ),
          borderWidth: 1.5,
          borderRadius: 6,
          hoverBackgroundColor: COLORS.orange,
        },
      ],
    }),
    [arr, weekday.labels, showRevenue, bestIdx],
  );

  const options = useMemo(
    () => ({
      ...baseOptions,
      plugins: {
        ...baseOptions.plugins,
        legend: { display: false },
        tooltip: {
          ...baseOptions.plugins.tooltip,
          callbacks: {
            title: ([item]) => item.label,
            label: ({ raw }) =>
              showRevenue
                ? ` ${CLP(raw)}`
                : ` ${raw.toLocaleString("es-CL")} ventas`,
          },
        },
      },
      scales: {
        ...baseOptions.scales,
        y: {
          ...baseOptions.scales.y,
          beginAtZero: true,
          title: {
            display: true,
            text: showRevenue ? "Ingreso sin IVA (CLP)" : "Cantidad de ventas",
            color: COLORS.text,
            font: { size: 11 },
          },
          ticks: {
            ...baseOptions.scales.y.ticks,
            callback: showRevenue
              ? (v) => `$${(v / 1_000_000).toFixed(1)}M`
              : undefined,
          },
        },
        x: { ...baseOptions.scales.x },
      },
    }),
    [showRevenue],
  );

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "baseline", gap: 1.5, mb: 2 }}>
        <Typography variant="subtitle2">
          {showRevenue
            ? "Ingresos Acumulados por Día de la Semana"
            : "Ventas Acumuladas por Día de la Semana"}
        </Typography>
        {bestIdx >= 0 && (
          <Typography variant="caption" sx={{ color: COLORS.orange }}>
            Mejor día: {weekday.labels[bestIdx]}
          </Typography>
        )}
      </Box>
      <Box sx={{ height }}>
        <Bar data={data} options={options} />
      </Box>
    </Box>
  );
};

export default SalesByWeekday;
