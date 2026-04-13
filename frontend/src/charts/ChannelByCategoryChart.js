import React, { useMemo } from "react";
import { Bar } from "react-chartjs-2";
import { Box, Typography } from "@mui/material";
import { useChartConfig, CLP } from "./chartConfig";

const CHANNEL_STYLE = {
  "Uber Eats": { bg: "#3B82F680", border: "#3B82F6" },
  Local: { bg: "#22C55E80", border: "#22C55E" },
};

const ChannelByCategoryChart = ({
  channelByCategory,
  showRevenue = false,
  height = 260,
}) => {
  const { colors, baseOptions: bOpts } = useChartConfig();
  const CATS = ["Especialidades", "Extras"];
  const CHANNELS = ["Uber Eats", "Local"];

  const metric = showRevenue ? "revenue" : "units";
  const formatter = showRevenue
    ? CLP
    : (v) => `${v.toLocaleString("es-CL")} uds.`;
  const ylabel = showRevenue ? "Ingreso s/IVA (CLP)" : "Unidades vendidas";

  const data = useMemo(() => {
    if (!channelByCategory) return null;
    return {
      labels: CATS,
      datasets: CHANNELS.map((ch) => ({
        label: ch,
        data: CATS.map((cat) => channelByCategory[cat]?.[ch]?.[metric] ?? 0),
        backgroundColor: CHANNEL_STYLE[ch].bg,
        borderColor: CHANNEL_STYLE[ch].border,
        borderWidth: 1.5,
        borderRadius: 4,
      })),
    };
  }, [channelByCategory, metric]);

  const options = useMemo(
    () => ({
      ...bOpts,
      plugins: {
        ...bOpts.plugins,
        legend: { ...bOpts.plugins.legend, position: "top" },
        tooltip: {
          ...bOpts.plugins.tooltip,
          callbacks: {
            label: ({ dataset, raw }) => ` ${dataset.label}: ${formatter(raw)}`,
          },
        },
      },
      scales: {
        x: { ...bOpts.scales.x, grid: { color: "transparent" } },
        y: {
          ...bOpts.scales.y,
          title: {
            display: true,
            text: ylabel,
            color: colors.text,
            font: { size: 11 },
          },
        },
      },
    }),
    [bOpts, colors, showRevenue],
  );

  if (!data) return null;

  const title = showRevenue
    ? "Ingresos por Categoría y Canal (s/IVA)"
    : "Unidades por Categoría y Canal";

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 2 }}>
        {title}
      </Typography>
      <Box sx={{ height }}>
        <Bar data={data} options={options} />
      </Box>
    </Box>
  );
};

export default ChannelByCategoryChart;
