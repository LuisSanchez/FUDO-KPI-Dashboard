import React, { useMemo } from "react";
import { Bar } from "react-chartjs-2";
import { Box, Typography } from "@mui/material";
import { useChartConfig, COLORS, CLP } from "./chartConfig";

const RevenueByHour = ({ hourly, height = 260 }) => {
  const { colors, baseOptions: bOpts } = useChartConfig();

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
      ...bOpts,
      plugins: {
        ...bOpts.plugins,
        legend: { display: false },
        tooltip: {
          ...bOpts.plugins.tooltip,
          callbacks: {
            title: ([item]) => `Hora: ${item.label}`,
            label: ({ raw }) => ` ${CLP(raw)}`,
          },
        },
      },
      scales: {
        ...bOpts.scales,
        y: {
          ...bOpts.scales.y,
          beginAtZero: true,
          title: {
            display: true,
            text: "Ingreso sin IVA (CLP)",
            color: colors.text,
            font: { size: 11 },
          },
          ticks: {
            ...bOpts.scales.y.ticks,
            callback: (v) => `$${(v / 1000).toFixed(0)}K`,
          },
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
        Ingresos por Hora del Día (sin IVA)
      </Typography>
      <Box sx={{ height }}>
        <Bar data={data} options={options} />
      </Box>
    </Box>
  );
};

export default RevenueByHour;
