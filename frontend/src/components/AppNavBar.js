import React, { useState } from "react";
import {
  AppBar,
  Toolbar,
  Box,
  Typography,
  Button,
  Tooltip,
  IconButton,
  Menu,
  MenuItem,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import LocalPizzaIcon from "@mui/icons-material/LocalPizza";
import TableChartIcon from "@mui/icons-material/TableChart";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import PriceCheckIcon from "@mui/icons-material/PriceCheck";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import TableViewIcon from "@mui/icons-material/TableView";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import DownloadIcon from "@mui/icons-material/Download";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import TravelExploreIcon from "@mui/icons-material/TravelExplore";
import RefreshIcon from "@mui/icons-material/Refresh";
import Brightness4Icon from "@mui/icons-material/Brightness4";
import Brightness7Icon from "@mui/icons-material/Brightness7";

const AppNavBar = ({
  bothUploaded,
  hasAnyFile,
  pdfLoading,
  excelLoading,
  onOpenSalesTable,
  onOpenExpensesTable,
  onOpenPricesTable,
  onDownloadPdf,
  onDownloadExcel,
  onOpenHelp,
  onStartTour,
  onReset,
  colorMode,
  onToggleMode,
}) => {
  const [menuAnchor, setMenuAnchor] = useState(null);
  const theme = useTheme();
  const isSmall = useMediaQuery(theme.breakpoints.down("sm"));

  const closeMenu = () => setMenuAnchor(null);

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        bgcolor: "background.default",
        borderBottom: "1px solid",
        borderColor: "divider",
      }}
    >
      <Toolbar
        sx={{
          maxWidth: 1200,
          mx: "auto",
          width: "100%",
          px: { xs: 1, md: 4 },
          gap: { xs: 0.5, md: 1 },
          minHeight: { xs: 56, sm: 64 },
        }}
      >
        {/* Brand */}
        <LocalPizzaIcon
          sx={{ color: "primary.main", fontSize: { xs: 22, sm: 28 }, mr: 0.5 }}
        />
        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <Typography
            variant="h6"
            fontWeight={700}
            sx={{
              lineHeight: 1.2,
              fontSize: { xs: "0.95rem", sm: "1.25rem" },
              whiteSpace: "nowrap",
            }}
          >
            FUDO Analytics
          </Typography>
          {!isSmall && (
            <Typography variant="caption" color="text.secondary">
              Food Finance Dashboard
            </Typography>
          )}
        </Box>

        {/* Table buttons + Descargar — only when both files are loaded */}
        {bothUploaded && (
          <Box
            data-tour="appbar-tables"
            sx={{ display: "flex", alignItems: "center", gap: 0.5 }}
          >
            {isSmall ? (
              <>
                <Tooltip title="Ver tabla de ventas">
                  <IconButton
                    size="small"
                    onClick={onOpenSalesTable}
                    sx={{ color: "text.secondary" }}
                  >
                    <TableChartIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Ver tabla de gastos">
                  <IconButton
                    size="small"
                    onClick={onOpenExpensesTable}
                    sx={{ color: "text.secondary" }}
                  >
                    <ReceiptLongIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Ver precios y márgenes por producto">
                  <IconButton
                    size="small"
                    onClick={onOpenPricesTable}
                    sx={{ color: "text.secondary" }}
                  >
                    <PriceCheckIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </>
            ) : (
              <>
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
              </>
            )}

            {/* Descargar dropdown */}
            {isSmall ? (
              <Tooltip
                title={pdfLoading || excelLoading ? "Generando…" : "Descargar"}
              >
                <span>
                  <IconButton
                    size="small"
                    data-tour="pdf-button"
                    onClick={(e) => setMenuAnchor(e.currentTarget)}
                    disabled={pdfLoading || excelLoading}
                    sx={{
                      color: "primary.main",
                      border: "1px solid",
                      borderColor: "primary.main",
                      borderRadius: 1,
                    }}
                  >
                    <DownloadIcon fontSize="small" />
                  </IconButton>
                </span>
              </Tooltip>
            ) : (
              <Button
                size="small"
                data-tour="pdf-button"
                endIcon={<ArrowDropDownIcon />}
                onClick={(e) => setMenuAnchor(e.currentTarget)}
                disabled={pdfLoading || excelLoading}
                sx={{
                  color: "primary.main",
                  borderColor: "primary.main",
                  border: "1px solid",
                  "&:hover": { bgcolor: "#F9731620" },
                }}
              >
                {pdfLoading || excelLoading ? "Generando…" : "Descargar"}
              </Button>
            )}
            <Menu
              anchorEl={menuAnchor}
              open={!!menuAnchor}
              onClose={closeMenu}
              PaperProps={{
                sx: { border: "1px solid", borderColor: "divider" },
              }}
            >
              <MenuItem
                onClick={() => {
                  onDownloadPdf();
                  closeMenu();
                }}
                sx={{ gap: 1 }}
              >
                <PictureAsPdfIcon
                  fontSize="small"
                  sx={{ color: "primary.main" }}
                />
                Reporte del Mes
              </MenuItem>
              <MenuItem
                onClick={() => {
                  onDownloadExcel("Especialidades");
                  closeMenu();
                }}
                sx={{ gap: 1 }}
              >
                <TableViewIcon fontSize="small" sx={{ color: "#22C55E" }} />
                Especialidades (Excel)
              </MenuItem>
              <MenuItem
                onClick={() => {
                  onDownloadExcel("Extras");
                  closeMenu();
                }}
                sx={{ gap: 1 }}
              >
                <TableViewIcon fontSize="small" sx={{ color: "#38BDF8" }} />
                Extras (Excel)
              </MenuItem>
            </Menu>
          </Box>
        )}

        {/* Light / dark toggle */}
        <Tooltip title={colorMode === "dark" ? "Modo claro" : "Modo oscuro"}>
          <IconButton
            onClick={onToggleMode}
            size="small"
            sx={{ color: "text.secondary" }}
          >
            {colorMode === "dark" ? (
              <Brightness7Icon fontSize="small" />
            ) : (
              <Brightness4Icon fontSize="small" />
            )}
          </IconButton>
        </Tooltip>

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
};

export default AppNavBar;
