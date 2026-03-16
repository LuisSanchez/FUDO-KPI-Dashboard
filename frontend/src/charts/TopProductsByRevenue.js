import React, { useMemo } from 'react';
import { Bar } from 'react-chartjs-2';
import { Box, Typography } from '@mui/material';
import { horizontalBaseOptions, COLORS, PALETTE, CLP } from './chartConfig';

const TopProductsByRevenue = ({ top10Revenue }) => {
  const sorted = useMemo(
    () => [...top10Revenue].sort((a, b) => a.ingreso_sin_iva - b.ingreso_sin_iva),
    [top10Revenue],
  );

  const data = useMemo(() => ({
    labels: sorted.map((r) => r.Producto),
    datasets: [
      {
        label: 'Ingreso sin IVA',
        data: sorted.map((r) => r.ingreso_sin_iva),
        backgroundColor: sorted.map((_, i) => PALETTE[i % PALETTE.length] + '80'),
        borderColor:     sorted.map((_, i) => PALETTE[i % PALETTE.length]),
        borderWidth: 1.5,
        borderRadius: 4,
        hoverBackgroundColor: sorted.map((_, i) => PALETTE[i % PALETTE.length]),
      },
    ],
  }), [sorted]);

  const options = useMemo(() => ({
    ...horizontalBaseOptions,
    plugins: {
      ...horizontalBaseOptions.plugins,
      legend: { display: false },
      tooltip: {
        ...horizontalBaseOptions.plugins.tooltip,
        callbacks: {
          label: ({ raw }) => ` ${CLP(raw)}`,
        },
      },
    },
    scales: {
      ...horizontalBaseOptions.scales,
      x: {
        ...horizontalBaseOptions.scales.x,
        beginAtZero: true,
        title: { display: true, text: 'Ingreso sin IVA (CLP)', color: COLORS.text, font: { size: 11 } },
        ticks: {
          ...horizontalBaseOptions.scales.x.ticks,
          callback: (v) => `$${(v / 1_000_000).toFixed(1)}M`,
        },
      },
      y: {
        ...horizontalBaseOptions.scales.y,
        ticks: {
          ...horizontalBaseOptions.scales.y.ticks,
          font: { size: 11 },
          callback: (_, i) => {
            const label = sorted[i]?.Producto ?? '';
            return label.length > 22 ? label.slice(0, 20) + '…' : label;
          },
        },
      },
    },
  }), [sorted]);

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 2 }}>
        Top 10 Productos por Ingresos (sin IVA)
      </Typography>
      <Box sx={{ height: 320 }}>
        <Bar data={data} options={options} />
      </Box>
    </Box>
  );
};

export default TopProductsByRevenue;
