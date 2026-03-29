import React from "react";
import {
  AppBar,
  Toolbar,
  Box,
  Typography,
  Button,
  Tooltip,
  IconButton,
} from "@mui/material";
import LocalPizzaIcon from "@mui/icons-material/LocalPizza";
import TableChartIcon from "@mui/icons-material/TableChart";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import PriceCheckIcon from "@mui/icons-material/PriceCheck";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import TravelExploreIcon from "@mui/icons-material/TravelExplore";
import RefreshIcon from "@mui/icons-material/Refresh";

const AppNavBar = ({
  bothUploaded,
  hasAnyFile,
  pdfLoading,
  onOpenSalesTable,
  onOpenExpensesTable,
  onOpenPricesTable,
  onDownloadPdf,
  onOpenHelp,
  onStartTour,
  onReset,
}) => (
  <AppBar
    position="static"
    elevation={0}
    sx={{ bgcolor: "#0F172A", borderBottom: "1px solid #1E293B" }}
  >
    <Toolbar
      sx={{
        maxWidth: 1200,
        mx: "auto",
        width: "100%",
        px: { xs: 2, md: 4 },
        gap: 1,
      }}
    >
      {/* Brand */}
      <LocalPizzaIcon sx={{ color: "primary.main", fontSize: 28 }} />
      <Box sx={{ flexGrow: 1 }}>
        <Typography variant="h6" fontWeight={700} sx={{ lineHeight: 1.2 }}>
          FUDO Analytics
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Food Finance Dashboard
        </Typography>
      </Box>

      {/* Table buttons + PDF — only when both files are loaded */}
      {bothUploaded && (
        <Box
          data-tour="appbar-tables"
          sx={{ display: "flex", alignItems: "center", gap: 0.5 }}
        >
          <Tooltip title="Ver tabla de ventas">
            <Button
              size="small"
              startIcon={<TableChartIcon />}
              onClick={onOpenSalesTable}
              sx={{
                color: "text.secondary",
                "&:hover": { color: "text.primary" },
              }}
            >
              Ventas
            </Button>
          </Tooltip>
          <Tooltip title="Ver tabla de gastos">
            <Button
              size="small"
              startIcon={<ReceiptLongIcon />}
              onClick={onOpenExpensesTable}
              sx={{
                color: "text.secondary",
                "&:hover": { color: "text.primary" },
              }}
            >
              Gastos
            </Button>
          </Tooltip>
          <Tooltip title="Ver precios y márgenes por producto">
            <Button
              size="small"
              startIcon={<PriceCheckIcon />}
              onClick={onOpenPricesTable}
              sx={{
                color: "text.secondary",
                "&:hover": { color: "text.primary" },
              }}
            >
              Precios
            </Button>
          </Tooltip>
          <Tooltip title="Descargar reporte PDF">
            <Button
              size="small"
              data-tour="pdf-button"
              startIcon={<PictureAsPdfIcon />}
              onClick={onDownloadPdf}
              disabled={pdfLoading}
              sx={{
                color: "primary.main",
                borderColor: "primary.main",
                border: "1px solid",
                "&:hover": { bgcolor: "#F9731620" },
              }}
            >
              {pdfLoading ? "Generando…" : "PDF"}
            </Button>
          </Tooltip>
        </Box>
      )}

      {/* Icon actions — always visible */}
      <Tooltip title="Cómo funciona">
        <IconButton
          data-tour="help-button"
          onClick={onOpenHelp}
          size="small"
          sx={{ color: "text.secondary" }}
        >
          <HelpOutlineIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="Ver guía de inicio">
        <IconButton
          onClick={onStartTour}
          size="small"
          sx={{ color: "text.secondary" }}
        >
          <TravelExploreIcon />
        </IconButton>
      </Tooltip>
      {hasAnyFile && (
        <Tooltip title="Reiniciar datos">
          <IconButton
            onClick={onReset}
            size="small"
            sx={{ color: "text.secondary" }}
          >
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      )}
    </Toolbar>
  </AppBar>
);

export default AppNavBar;
