import React, { useMemo } from "react";
import { Bar } from "react-chartjs-2";
import { Box, Typography } from "@mui/material";
import { useChartConfig, COLORS, CLP } from "./chartConfig";

const SalesByDay = ({ daily, height = 260, showRevenue = false }) => {
  const { colors, baseOptions: bOpts } = useChartConfig();

  const bestDayIdx = useMemo(() => {
    const arr = showRevenue ? daily.revenue : daily.count;
    return arr.indexOf(Math.max(...arr));
  }, [daily, showRevenue]);

  const data = useMemo(() => {
    const arr = showRevenue ? daily.revenue : daily.count;
    return {
      labels: daily.labels.map((d) => `Día ${d}`),
      datasets: [
        {
          label: showRevenue ? "Ingreso sin IVA" : "Ventas (líneas)",
          data: arr,
          backgroundColor: arr.map((_, i) =>
            i === bestDayIdx ? COLORS.orange : COLORS.orangeFade,
          ),
          borderColor: arr.map((_, i) =>
            i === bestDayIdx ? COLORS.orange : COLORS.orange + "80",
          ),
          borderWidth: 1.5,
          borderRadius: 4,
          hoverBackgroundColor: COLORS.orange,
        },
      ],
    };
  }, [daily, showRevenue, bestDayIdx]);

  const options = useMemo(
    () => ({
      ...bOpts,
      plugins: {
        ...bOpts.plugins,
        legend: { display: false },
        tooltip: {
          ...bOpts.plugins.tooltip,
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
        ...bOpts.scales,
        y: {
          ...bOpts.scales.y,
          beginAtZero: true,
          title: {
            display: true,
            text: showRevenue ? "Ingreso sin IVA (CLP)" : "Cantidad de ventas",
            color: colors.text,
            font: { size: 11 },
          },
          ticks: {
            ...bOpts.scales.y.ticks,
            callback: showRevenue
              ? (v) => `$${(v / 1_000_000).toFixed(1)}M`
              : undefined,
          },
        },
        x: {
          ...bOpts.scales.x,
          title: {
            display: true,
            text: "Día del mes",
            color: colors.text,
            font: { size: 11 },
          },
        },
      },
    }),
    [showRevenue, bOpts, colors],
  );

  const bestDay = daily.labels[bestDayIdx];

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "baseline", gap: 1.5, mb: 2 }}>
        <Typography variant="subtitle2">
          {showRevenue ? "Ingresos por Día" : "Ventas por Día del Mes"}
        </Typography>
        {bestDay != null && (
          <Typography variant="caption" sx={{ color: COLORS.orange }}>
            Mejor día: {bestDay}
          </Typography>
        )}
      </Box>
      <Box sx={{ height }}>
        <Bar data={data} options={options} />
      </Box>
    </Box>
  );
};

export default SalesByDay;
