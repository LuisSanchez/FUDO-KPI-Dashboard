import React, { useMemo } from "react";
import { Bar } from "react-chartjs-2";
import { Box, Typography } from "@mui/material";
import { baseOptions, COLORS, CLP } from "./chartConfig";

const RevenueByHour = ({ hourly, height = 260 }) => {
  const data = useMemo(
    () => ({
      labels: hourly.labels.map((h) => `${String(h).padStart(2, "0")}:00`),
      datasets: [
        {
          label: "Ingreso sin IVA",
          data: hourly.revenue,
          backgroundColor: COLORS.blueFade,
          borderColor: COLORS.blue,
          borderWidth: 1.5,
          borderRadius: 4,
          hoverBackgroundColor: COLORS.blue,
        },
      ],
    }),
    [hourly],
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
            title: ([item]) => `Hora: ${item.label}`,
            label: ({ raw }) => ` ${CLP(raw)}`,
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
            text: "Ingreso sin IVA (CLP)",
            color: COLORS.text,
            font: { size: 11 },
          },
          ticks: {
            ...baseOptions.scales.y.ticks,
            callback: (v) => `$${(v / 1000).toFixed(0)}K`,
          },
        },
        x: {
          ...baseOptions.scales.x,
          title: {
            display: true,
            text: "Hora del día",
            color: COLORS.text,
            font: { size: 11 },
          },
          min: 10,
        },
      },
    }),
    [],
  );

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 2 }}>
        Ingresos por Hora del Día (sin IVA)
      </Typography>
      <Box sx={{ height }}>
        <Bar data={data} options={options} />
      </Box>
    </Box>
  );
};

export default RevenueByHour;
