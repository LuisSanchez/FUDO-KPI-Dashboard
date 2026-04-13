import React, { useMemo } from "react";
import { Doughnut } from "react-chartjs-2";
import { Box, Typography } from "@mui/material";
import { useChartConfig, CLP } from "./chartConfig";

const CHANNEL_COLORS = {
  "Uber Eats": { bg: "#3B82F6", fade: "#3B82F640" },
  Local: { bg: "#22C55E", fade: "#22C55E40" },
};

const HalfChart = ({ title, labels, values, formatter }) => {
  const { baseOptions: bOpts } = useChartConfig();

  const data = useMemo(
    () => ({
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: labels.map(
            (l) => CHANNEL_COLORS[l]?.fade ?? "#64748B40",
          ),
          borderColor: labels.map((l) => CHANNEL_COLORS[l]?.bg ?? "#64748B"),
          borderWidth: 2,
          hoverBackgroundColor: labels.map(
            (l) => CHANNEL_COLORS[l]?.bg ?? "#64748B",
          ),
        },
      ],
    }),
    [labels, values],
  );

  const options = useMemo(
    () => ({
      ...bOpts,
      cutout: "62%",
      plugins: {
        ...bOpts.plugins,
        legend: { ...bOpts.plugins.legend, position: "bottom" },
        tooltip: {
          ...bOpts.plugins.tooltip,
          callbacks: {
            label: ({ label, raw, dataset }) => {
              const total = dataset.data.reduce((a, b) => a + b, 0);
              const pct = total > 0 ? ((raw / total) * 100).toFixed(1) : 0;
              return ` ${label}: ${formatter(raw)} (${pct}%)`;
            },
          },
        },
      },
      scales: {},
    }),
    [bOpts, formatter],
  );

  return (
    <Box sx={{ flex: 1, minWidth: 0 }}>
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ display: "block", textAlign: "center", mb: 1 }}
      >
        {title}
      </Typography>
      <Box sx={{ height: 200 }}>
        <Doughnut data={data} options={options} />
      </Box>
    </Box>
  );
};

const ChannelSplitChart = ({ channelSplit, height = 280 }) => {
  if (!channelSplit) return null;
  const { labels, units, revenue } = channelSplit;

  const totalUnits = units.reduce((a, b) => a + b, 0);
  const uberUnits = units[labels.indexOf("Uber Eats")] ?? 0;
  const uberPct =
    totalUnits > 0 ? ((uberUnits / totalUnits) * 100).toFixed(1) : 0;

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
        Canal de Venta: Uber Eats vs Local
      </Typography>
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ display: "block", mb: 2 }}
      >
        {uberUnits.toLocaleString("es-CL")} uds. en Uber Eats ({uberPct}% del
        total)
      </Typography>
      <Box sx={{ display: "flex", gap: 2, height }}>
        <HalfChart
          title="Unidades vendidas"
          labels={labels}
          values={units}
          formatter={(v) => `${v.toLocaleString("es-CL")} uds.`}
        />
        <HalfChart
          title="Ingresos s/IVA"
          labels={labels}
          values={revenue}
          formatter={CLP}
        />
      </Box>
    </Box>
  );
};

export default ChannelSplitChart;
