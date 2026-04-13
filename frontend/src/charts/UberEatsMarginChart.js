import React, { useMemo } from "react";
import { Bar } from "react-chartjs-2";
import { Box, Typography } from "@mui/material";
import { useChartConfig } from "./chartConfig";

/**
 * Horizontal bar chart: one bar per product sold on Uber Eats,
 * coloured green (positive margin) or red (negative / losing money).
 */
const UberEatsMarginChart = ({ products = [], height = 360 }) => {
  const { colors, horizontalBaseOptions: hOpts } = useChartConfig();

  const sorted = useMemo(
    () => [...products].sort((a, b) => a.margen_pct - b.margen_pct),
    [products],
  );

  const data = useMemo(
    () => ({
      labels: sorted.map((r) => r.Producto),
      datasets: [
        {
          label: "Margen s/IVA %",
          data: sorted.map((r) => r.margen_pct),
          backgroundColor: sorted.map((r) =>
            r.margen_pct >= 0 ? "#22C55E60" : "#EF444460",
          ),
          borderColor: sorted.map((r) =>
            r.margen_pct >= 0 ? "#22C55E" : "#EF4444",
          ),
          borderWidth: 1.5,
          borderRadius: 4,
        },
      ],
    }),
    [sorted],
  );

  const options = useMemo(
    () => ({
      ...hOpts,
      plugins: {
        ...hOpts.plugins,
        legend: { display: false },
        tooltip: {
          ...hOpts.plugins.tooltip,
          callbacks: {
            label: ({ dataIndex, raw }) => {
              const p = sorted[dataIndex];
              return [
                ` Margen: ${raw.toFixed(1)}%`,
                ` Ingreso s/IVA: $${p.ingreso_sin_iva.toLocaleString("es-CL")}`,
                ` Costo ingredientes: $${p.costo_ingredientes.toLocaleString("es-CL")}`,
                ` Comisión Uber: $${p.comision_sin_iva.toLocaleString("es-CL")}`,
                ` Margen neto: $${p.margen_sin_iva.toLocaleString("es-CL")}`,
              ];
            },
          },
        },
      },
      scales: {
        ...hOpts.scales,
        x: {
          ...hOpts.scales.x,
          title: {
            display: true,
            text: "Margen %",
            color: colors.text,
            font: { size: 11 },
          },
          ticks: {
            ...hOpts.scales.x.ticks,
            callback: (v) => `${v}%`,
          },
        },
        y: {
          ...hOpts.scales.y,
          ticks: {
            ...hOpts.scales.y.ticks,
            font: { size: 10 },
            callback: (_, i) => {
              const label = sorted[i]?.Producto ?? "";
              return label.length > 22 ? label.slice(0, 20) + "…" : label;
            },
          },
        },
      },
    }),
    [sorted, hOpts, colors],
  );

  if (!products.length) return null;

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
        Margen por Producto en Uber Eats (s/IVA)
      </Typography>
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ display: "block", mb: 2 }}
      >
        Verde = ganando · Rojo = perdiendo dinero
      </Typography>
      <Box sx={{ height }}>
        <Bar data={data} options={options} />
      </Box>
    </Box>
  );
};

export default UberEatsMarginChart;
