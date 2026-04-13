import React, { useMemo } from "react";
import { Bar } from "react-chartjs-2";
import { Box, Typography } from "@mui/material";
import { useChartConfig, COLORS } from "./chartConfig";

const SalesByHour = ({ hourly, height = 260 }) => {
  const { colors, baseOptions: bOpts } = useChartConfig();

  const data = useMemo(
    () => ({
      labels: hourly.labels.map((h) => `${String(h).padStart(2, "0")}:00`),
      datasets: [
        {
          label: "Ventas (líneas)",
          data: hourly.count,
          backgroundColor: COLORS.orangeFade,
          borderColor: COLORS.orange,
          borderWidth: 1.5,
          borderRadius: 4,
          hoverBackgroundColor: COLORS.orange,
        },
      ],
    }),
    [hourly],
  );

  const options = useMemo(
    () => ({
      ...bOpts,
      plugins: {
        ...bOpts.plugins,
        legend: { display: false },
        tooltip: {
          ...bOpts.plugins.tooltip,
          callbacks: {
            title: ([item]) => `Hora: ${item.label}`,
            label: ({ raw }) => ` ${raw.toLocaleString("es-CL")} ventas`,
          },
        },
      },
      scales: {
        ...bOpts.scales,
        y: {
          ...bOpts.scales.y,
          title: {
            display: true,
            text: "Cantidad de ventas",
            color: colors.text,
            font: { size: 11 },
          },
          beginAtZero: true,
        },
        x: {
          ...bOpts.scales.x,
          title: {
            display: true,
            text: "Hora del día",
            color: colors.text,
            font: { size: 11 },
          },
          min: 10,
        },
      },
    }),
    [bOpts, colors],
  );

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 2 }}>
        Ventas por Hora del Día
      </Typography>
      <Box sx={{ height }}>
        <Bar data={data} options={options} />
      </Box>
    </Box>
  );
};

export default SalesByHour;
