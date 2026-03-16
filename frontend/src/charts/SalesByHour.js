import React, { useMemo } from 'react';
import { Bar } from 'react-chartjs-2';
import { Box, Typography } from '@mui/material';
import { baseOptions, COLORS } from './chartConfig';

const SalesByHour = ({ hourly }) => {
  const data = useMemo(() => ({
    labels: hourly.labels.map((h) => `${String(h).padStart(2, '0')}:00`),
    datasets: [
      {
        label: 'Ventas (líneas)',
        data: hourly.count,
        backgroundColor: COLORS.orangeFade,
        borderColor: COLORS.orange,
        borderWidth: 1.5,
        borderRadius: 4,
        hoverBackgroundColor: COLORS.orange,
      },
    ],
  }), [hourly]);

  const options = useMemo(() => ({
    ...baseOptions,
    plugins: {
      ...baseOptions.plugins,
      legend: { display: false },
      tooltip: {
        ...baseOptions.plugins.tooltip,
        callbacks: {
          title: ([item]) => `Hora: ${item.label}`,
          label: ({ raw }) => ` ${raw.toLocaleString('es-CL')} líneas de venta`,
        },
      },
    },
    scales: {
      ...baseOptions.scales,
      y: {
        ...baseOptions.scales.y,
        title: { display: true, text: 'Cantidad de líneas', color: COLORS.text, font: { size: 11 } },
        beginAtZero: true,
      },
      x: {
        ...baseOptions.scales.x,
        title: { display: true, text: 'Hora del día', color: COLORS.text, font: { size: 11 } },
      },
    },
  }), []);

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 2 }}>
        Ventas por Hora del Día
      </Typography>
      <Box sx={{ height: 260 }}>
        <Bar data={data} options={options} />
      </Box>
    </Box>
  );
};

export default SalesByHour;
