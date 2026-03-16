import React, { useMemo } from "react";
import { Doughnut } from "react-chartjs-2";
import { Box, Typography } from "@mui/material";
import { COLORS, PALETTE } from "./chartConfig";

const DEFAULT_HEIGHT = 320;

const ProductDistribution = ({ pieQuantity, height = DEFAULT_HEIGHT }) => {
  const data = useMemo(
    () => ({
      labels: pieQuantity.labels,
      datasets: [
        {
          label: "Unidades vendidas",
          data: pieQuantity.values,
          backgroundColor: PALETTE.map((c) => c + "CC"),
          borderColor: PALETTE,
          borderWidth: 1.5,
          hoverOffset: 8,
          hoverBorderWidth: 2,
        },
      ],
    }),
    [pieQuantity],
  );

  const total = useMemo(
    () => pieQuantity.values.reduce((s, v) => s + v, 0),
    [pieQuantity],
  );

  const options = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      cutout: "62%",
      plugins: {
        legend: {
          position: "right",
          labels: {
            color: COLORS.textPrimary,
            font: { family: '"Inter", "Roboto", sans-serif', size: 11 },
            boxWidth: 12,
            padding: 10,
            generateLabels: (chart) =>
              chart.data.labels.map((label, i) => {
                const value = chart.data.datasets[0].data[i];
                const pct =
                  total > 0 ? ((value / total) * 100).toFixed(1) : "0";
                return {
                  text: `${label.length > 18 ? label.slice(0, 16) + "…" : label} (${pct}%)`,
                  fillStyle: PALETTE[i % PALETTE.length] + "CC",
                  strokeStyle: PALETTE[i % PALETTE.length],
                  lineWidth: 1.5,
                  index: i,
                  fontColor: COLORS.textPrimary,
                };
              }),
          },
        },
        tooltip: {
          backgroundColor: "#0F172A",
          borderColor: "#334155",
          borderWidth: 1,
          titleColor: COLORS.textPrimary,
          bodyColor: COLORS.text,
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: ({ raw, label }) => {
              const pct = total > 0 ? ((raw / total) * 100).toFixed(1) : "0";
              return ` ${raw.toLocaleString("es-CL")} uds. (${pct}%)`;
            },
          },
        },
      },
    }),
    [total],
  );

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 2 }}>
        Distribución de Unidades por Producto (Top 10)
      </Typography>
      <Box sx={{ height }}>
        <Doughnut data={data} options={options} />
      </Box>
    </Box>
  );
};

export default ProductDistribution;
