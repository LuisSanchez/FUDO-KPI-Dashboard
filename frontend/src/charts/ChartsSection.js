/**
 * ChartsSection — fetches chart data from the backend and renders all 6 charts.
 * Chart.js components are registered once here via chartConfig import.
 */
import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  Divider,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
} from "@mui/material";
import BarChartIcon from "@mui/icons-material/BarChart";
import OpenInFullIcon from "@mui/icons-material/OpenInFull";
import CloseIcon from "@mui/icons-material/Close";

// Central registration (must run before any chart renders)
import "./chartConfig";

import SalesByDay from "./SalesByDay";
import SalesByHour from "./SalesByHour";
import RevenueByHour from "./RevenueByHour";
import TopProductsByQuantity from "./TopProductsByQuantity";
import TopProductsByRevenue from "./TopProductsByRevenue";
import ProductDistribution from "./ProductDistribution";
import QuantityVsRevenue from "./QuantityVsRevenue";

const MODAL_CHART_HEIGHT = 480;

const ChartCard = ({ title, children, modalContent, onOpenModal }) => (
  <Paper
    elevation={0}
    sx={{
      p: 3,
      border: "1px solid #1E3A5F",
      height: "100%",
      position: "relative",
    }}
  >
    {modalContent != null && (
      <IconButton
        size="small"
        onClick={onOpenModal}
        sx={{
          position: "absolute",
          top: 8,
          right: 8,
          color: "text.secondary",
          "&:hover": { color: "primary.main" },
        }}
        aria-label="Maximizar"
      >
        <OpenInFullIcon fontSize="small" />
      </IconButton>
    )}
    {children}
  </Paper>
);

const ChartsSection = ({ salesLoaded, selectedMonth }) => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [modalChart, setModalChart] = useState(null); // { title, content }

  const fetchCharts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params =
        selectedMonth && selectedMonth !== "all"
          ? `?month=${selectedMonth}`
          : "";
      const res = await axios.get(`/api/data/charts/${params}`);
      setChartData(res.data);
    } catch (err) {
      setError(err.response?.data?.error || "Error al cargar los gráficos");
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
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 3 }}>
        <BarChartIcon sx={{ color: "primary.main" }} />
        <Typography variant="h6" fontWeight={700}>
          Análisis Visual
        </Typography>
        <Divider sx={{ flexGrow: 1, ml: 1 }} />
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
          <CircularProgress color="primary" />
        </Box>
      )}

      {!loading && chartData && (
        <>
          <Box
            sx={{
              display: "flex",
              flexWrap: "wrap",
              gap: 3,
              width: "100%",
            }}
          >
            {[
              {
                key: "salesByDay",
                title: "Ventas por Día del Mes",
                card: <SalesByDay daily={chartData.daily} />,
                modal: (
                  <SalesByDay
                    daily={chartData.daily}
                    height={MODAL_CHART_HEIGHT}
                  />
                ),
              },
              {
                key: "revenueByDay",
                title: "Ingresos por Día del Mes (sin IVA)",
                card: <SalesByDay daily={chartData.daily} showRevenue />,
                modal: (
                  <SalesByDay
                    daily={chartData.daily}
                    showRevenue
                    height={MODAL_CHART_HEIGHT}
                  />
                ),
              },
              {
                key: "salesByHour",
                title: "Ventas por Hora del Día",
                card: <SalesByHour hourly={chartData.hourly} />,
                modal: (
                  <SalesByHour
                    hourly={chartData.hourly}
                    height={MODAL_CHART_HEIGHT}
                  />
                ),
              },
              {
                key: "revenueByHour",
                title: "Ingresos por Hora del Día (sin IVA)",
                card: <RevenueByHour hourly={chartData.hourly} />,
                modal: (
                  <RevenueByHour
                    hourly={chartData.hourly}
                    height={MODAL_CHART_HEIGHT}
                  />
                ),
              },
              {
                key: "topQty",
                title: "Top 10 Productos por Unidades Vendidas",
                card: (
                  <TopProductsByQuantity
                    top10Quantity={chartData.top10_quantity}
                  />
                ),
                modal: (
                  <TopProductsByQuantity
                    top10Quantity={chartData.top10_quantity}
                    height={MODAL_CHART_HEIGHT}
                  />
                ),
              },
              {
                key: "topRev",
                title: "Top 10 Productos por Ingresos (sin IVA)",
                card: (
                  <TopProductsByRevenue
                    top10Revenue={chartData.top10_revenue}
                  />
                ),
                modal: (
                  <TopProductsByRevenue
                    top10Revenue={chartData.top10_revenue}
                    height={MODAL_CHART_HEIGHT}
                  />
                ),
              },
              {
                key: "distribution",
                title: "Distribución de Unidades por Producto (Top 10)",
                card: (
                  <ProductDistribution pieQuantity={chartData.pie_quantity} />
                ),
                modal: (
                  <ProductDistribution
                    pieQuantity={chartData.pie_quantity}
                    height={MODAL_CHART_HEIGHT}
                  />
                ),
              },
              {
                key: "scatter",
                title: "Cantidad vs. Ingresos por Producto",
                card: <QuantityVsRevenue scatter={chartData.scatter} />,
                modal: (
                  <QuantityVsRevenue
                    scatter={chartData.scatter}
                    height={MODAL_CHART_HEIGHT}
                  />
                ),
              },
            ].map(({ key, title, card, modal }) => (
              <Box
                key={key}
                sx={{
                  flex: "0 0 calc(50% - 12px)",
                  minWidth: 0,
                  "@media (max-width: 600px)": { flex: "0 0 100%" },
                }}
              >
                <ChartCard
                  title={title}
                  modalContent={key}
                  onOpenModal={() => setModalChart({ title, content: modal })}
                >
                  {card}
                </ChartCard>
              </Box>
            ))}
          </Box>

          <Dialog
            open={!!modalChart}
            onClose={() => setModalChart(null)}
            maxWidth="md"
            fullWidth
            PaperProps={{
              sx: { bgcolor: "#1E293B", border: "1px solid #334155" },
            }}
          >
            <DialogTitle
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                pr: 1,
              }}
            >
              <Typography variant="h6">{modalChart?.title}</Typography>
              <IconButton
                size="small"
                onClick={() => setModalChart(null)}
                aria-label="Cerrar"
              >
                <CloseIcon />
              </IconButton>
            </DialogTitle>
            <DialogContent sx={{ pt: 0 }}>{modalChart?.content}</DialogContent>
          </Dialog>
        </>
      )}
    </Box>
  );
};

export default ChartsSection;
