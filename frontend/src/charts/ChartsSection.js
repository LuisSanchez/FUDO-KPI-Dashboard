/**
 * ChartsSection — fetches chart data from the backend and renders all 6 charts.
 * Chart.js components are registered once here via chartConfig import.
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  Box, Grid, Paper, Typography,
  CircularProgress, Alert, Divider,
} from '@mui/material';
import BarChartIcon from '@mui/icons-material/BarChart';

// Central registration (must run before any chart renders)
import './chartConfig';

import SalesByHour         from './SalesByHour';
import RevenueByHour       from './RevenueByHour';
import TopProductsByQuantity from './TopProductsByQuantity';
import TopProductsByRevenue  from './TopProductsByRevenue';
import ProductDistribution from './ProductDistribution';
import QuantityVsRevenue   from './QuantityVsRevenue';

const ChartCard = ({ children }) => (
  <Paper
    elevation={0}
    sx={{ p: 3, border: '1px solid #1E3A5F', height: '100%' }}
  >
    {children}
  </Paper>
);

const ChartsSection = ({ salesLoaded, selectedMonth }) => {
  const [chartData, setChartData] = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState(null);

  const fetchCharts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = selectedMonth && selectedMonth !== 'all'
        ? `?month=${selectedMonth}` : '';
      const res = await axios.get(`/api/data/charts/${params}`);
      setChartData(res.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar los gráficos');
    } finally {
      setLoading(false);
    }
  }, [selectedMonth]);

  useEffect(() => {
    if (salesLoaded) fetchCharts();
  }, [salesLoaded, fetchCharts]);

  if (!salesLoaded) return null;

  return (
    <Box sx={{ mt: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <BarChartIcon sx={{ color: 'primary.main' }} />
        <Typography variant="h6" fontWeight={700}>Análisis Visual</Typography>
        <Divider sx={{ flexGrow: 1, ml: 1 }} />
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress color="primary" />
        </Box>
      )}

      {!loading && chartData && (
        <Grid container spacing={3}>

          {/* Row 1: Hourly charts */}
          <Grid item xs={12} md={6}>
            <ChartCard>
              <SalesByHour hourly={chartData.hourly} />
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={6}>
            <ChartCard>
              <RevenueByHour hourly={chartData.hourly} />
            </ChartCard>
          </Grid>

          {/* Row 2: Top 10 bar charts */}
          <Grid item xs={12} md={6}>
            <ChartCard>
              <TopProductsByQuantity top10Quantity={chartData.top10_quantity} />
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={6}>
            <ChartCard>
              <TopProductsByRevenue top10Revenue={chartData.top10_revenue} />
            </ChartCard>
          </Grid>

          {/* Row 3: Pie + Scatter */}
          <Grid item xs={12} md={5}>
            <ChartCard>
              <ProductDistribution pieQuantity={chartData.pie_quantity} />
            </ChartCard>
          </Grid>
          <Grid item xs={12} md={7}>
            <ChartCard>
              <QuantityVsRevenue scatter={chartData.scatter} />
            </ChartCard>
          </Grid>

        </Grid>
      )}
    </Box>
  );
};

export default ChartsSection;
