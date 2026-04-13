import React, { useMemo } from "react";
import { Scatter } from "react-chartjs-2";
import { Box, Typography } from "@mui/material";
import { useChartConfig, COLORS, CLP } from "./chartConfig";

const QuantityVsRevenue = ({ scatter, height = 320 }) => {
  const { colors, baseOptions: bOpts } = useChartConfig();

  const data = useMemo(
    () => ({
      datasets: [
        {
          label: "Producto",
          data: scatter.map((r) => ({
            x: r.cantidad,
            y: r.ingreso_sin_iva,
            label: r.Producto,
          })),
          backgroundColor: COLORS.orangeFade,
          borderColor: COLORS.orange,
          borderWidth: 1.5,
          pointRadius: 6,
          pointHoverRadius: 9,
          hoverBackgroundColor: COLORS.orange,
        },
      ],
    }),
    [scatter],
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
            title: ([item]) => item.raw.label,
            label: ({ raw }) => [
              `Cantidad: ${raw.x.toLocaleString("es-CL")} uds.`,
              `Ingreso: ${CLP(raw.y)}`,
            ],
          },
        },
      },
      scales: {
        x: {
          ...bOpts.scales.x,
          beginAtZero: true,
          title: {
            display: true,
            text: "Unidades vendidas",
            color: colors.text,
            font: { size: 11 },
          },
          ticks: {
            ...bOpts.scales.x.ticks,
            callback: (v) => v.toLocaleString("es-CL"),
          },
        },
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
            callback: (v) => `$${(v / 1_000_000).toFixed(1)}M`,
          },
        },
      },
    }),
    [bOpts, colors],
  );

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
        Cantidad vs. Ingresos por Producto
      </Typography>
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ display: "block", mb: 2 }}
      >
        Top 40 productos por ingresos · pasa el cursor sobre un punto para ver
        el producto
      </Typography>
      <Box sx={{ height }}>
        <Scatter data={data} options={options} />
      </Box>
    </Box>
  );
};

export default QuantityVsRevenue;
