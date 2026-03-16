import React, { useMemo } from 'react';
import { Bar } from 'react-chartjs-2';
import { Box, Typography } from '@mui/material';
import { horizontalBaseOptions, COLORS, PALETTE } from './chartConfig';

const TopProductsByQuantity = ({ top10Quantity }) => {
  const sorted = useMemo(
    () => [...top10Quantity].sort((a, b) => a.cantidad - b.cantidad),
    [top10Quantity],
  );

  const data = useMemo(() => ({
    labels: sorted.map((r) => r.Producto),
    datasets: [
      {
        label: 'Unidades vendidas',
        data: sorted.map((r) => r.cantidad),
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
          label: ({ raw }) => ` ${raw.toLocaleString('es-CL')} unidades`,
        },
      },
    },
    scales: {
      ...horizontalBaseOptions.scales,
      x: {
        ...horizontalBaseOptions.scales.x,
        beginAtZero: true,
        title: { display: true, text: 'Unidades', color: COLORS.text, font: { size: 11 } },
      },
      y: {
        ...horizontalBaseOptions.scales.y,
        ticks: {
          ...horizontalBaseOptions.scales.y.ticks,
          font: { size: 11 },
          callback: (_, i, ticks) => {
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
        Top 10 Productos por Unidades Vendidas
      </Typography>
      <Box sx={{ height: 320 }}>
        <Bar data={data} options={options} />
      </Box>
    </Box>
  );
};

export default TopProductsByQuantity;
