import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Box,
  Typography,
  Chip,
  IconButton,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableCell,
  TableRow,
  TableSortLabel,
  Tooltip,
} from "@mui/material";
import TableChartIcon from "@mui/icons-material/TableChart";
import CloseIcon from "@mui/icons-material/Close";
import { CLP, fmtMonth, cmvColor } from "../utils/formatters";

const COLS = [
  { id: "Producto", label: "Producto", numeric: false },
  { id: "Categoría", label: "Categoría", numeric: false },
  { id: "cantidad", label: "Cant.", numeric: true },
  { id: "ingreso_sin_iva", label: "Ingreso s/IVA", numeric: true },
  { id: "cmv_pct", label: "CMV%", numeric: true },
  { id: "cmv", label: "CMV $", numeric: true },
  { id: "comision_pct", label: "Comis.%", numeric: true },
  { id: "margen_pct", label: "Margen%", numeric: true },
  { id: "margen_sin_iva", label: "Margen $", numeric: true },
];

const pct = (num, denom) =>
  denom > 0 ? ((num / denom) * 100).toFixed(1) : "—";

const SalesTableModal = ({ open, onClose, data, month }) => {
  const [orderBy, setOrderBy] = useState("ingreso_sin_iva");
  const [order, setOrder] = useState("desc");

  const handleSort = (col) => {
    if (orderBy === col) setOrder((o) => (o === "asc" ? "desc" : "asc"));
    else {
      setOrderBy(col);
      setOrder("desc");
    }
  };

  const sorted = [...(data || [])].sort((a, b) =>
    order === "asc" ? a[orderBy] - b[orderBy] : b[orderBy] - a[orderBy],
  );

  const totals = sorted.reduce(
    (acc, r) => ({
      cantidad: acc.cantidad + r.cantidad,
      ingreso_sin_iva: acc.ingreso_sin_iva + r.ingreso_sin_iva,
      cmv: acc.cmv + r.cmv,
      margen_sin_iva: acc.margen_sin_iva + r.margen_sin_iva,
      comision: acc.comision + r.comision,
    }),
    { cantidad: 0, ingreso_sin_iva: 0, cmv: 0, margen_sin_iva: 0, comision: 0 },
  );

  const totalCmvPct = pct(totals.cmv, totals.ingreso_sin_iva);
  const totalComisionPct = pct(totals.comision / 1.19, totals.ingreso_sin_iva);
  const totalMarPct = pct(totals.margen_sin_iva, totals.ingreso_sin_iva);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xl"
      fullWidth
      PaperProps={{
        sx: {
          bgcolor: "#1E293B",
          border: "1px solid #334155",
          maxHeight: "90vh",
        },
      }}
    >
      <DialogTitle
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <TableChartIcon color="primary" />
          <Typography variant="h6">
            Ventas por Producto
            {month && month !== "all" ? ` — ${fmtMonth(month)}` : ""}
          </Typography>
          <Chip
            label={`${sorted.length} productos`}
            size="small"
            variant="outlined"
          />
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        <TableContainer sx={{ maxHeight: "70vh" }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                {COLS.map((c) => (
                  <TableCell key={c.id} align={c.numeric ? "right" : "left"}>
                    <TableSortLabel
                      active={orderBy === c.id}
                      direction={orderBy === c.id ? order : "desc"}
                      onClick={() => c.numeric && handleSort(c.id)}
                      hideSortIcon={!c.numeric}
                    >
                      {c.label}
                    </TableSortLabel>
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {sorted.map((row, i) => (
                <TableRow
                  key={i}
                  hover
                  sx={{ "&:hover": { bgcolor: "#ffffff08" } }}
                >
                  <TableCell sx={{ fontWeight: 500 }}>{row.Producto}</TableCell>
                  <TableCell>
                    <Chip
                      label={row.Categoría}
                      size="small"
                      sx={{ fontSize: "0.65rem", height: 18 }}
                    />
                  </TableCell>
                  <TableCell align="right">
                    {row.cantidad.toLocaleString("es-CL")}
                  </TableCell>
                  <TableCell align="right">
                    {CLP(row.ingreso_sin_iva)}
                  </TableCell>
                  <TableCell align="right">
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "flex-end",
                        gap: 0.5,
                      }}
                    >
                      {row.cmv_pct === 0 && (
                        <Tooltip title="CMV 0%: este producto no tiene costo de ingredientes registrado en FUDO. Puede ser un error de configuración.">
                          <Typography
                            variant="caption"
                            sx={{
                              color: "warning.main",
                              fontWeight: 700,
                              cursor: "help",
                            }}
                          >
                            ⚠
                          </Typography>
                        </Tooltip>
                      )}
                      <Chip
                        label={`${row.cmv_pct}%`}
                        size="small"
                        color={
                          row.cmv_pct === 0 ? "warning" : cmvColor(row.cmv_pct)
                        }
                        sx={{ fontSize: "0.65rem", height: 20 }}
                      />
                    </Box>
                  </TableCell>
                  <TableCell align="right">{CLP(row.cmv)}</TableCell>
                  <TableCell align="right">
                    <Typography
                      variant="caption"
                      sx={{
                        color:
                          row.comision_pct > 0
                            ? "error.main"
                            : "text.secondary",
                        fontWeight: row.comision_pct > 0 ? 600 : 400,
                      }}
                    >
                      {row.comision_pct > 0 ? `${row.comision_pct}%` : "—"}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography
                      variant="caption"
                      sx={{
                        color:
                          row.margen_pct >= 50
                            ? "success.main"
                            : row.margen_pct >= 30
                              ? "warning.main"
                              : "error.main",
                        fontWeight: 600,
                      }}
                    >
                      {row.margen_pct}%
                    </Typography>
                  </TableCell>
                  <TableCell align="right">{CLP(row.margen_sin_iva)}</TableCell>
                </TableRow>
              ))}

              {/* Totals row */}
              <TableRow
                sx={{ bgcolor: "#0F172A", position: "sticky", bottom: 0 }}
              >
                <TableCell
                  colSpan={2}
                  sx={{ fontWeight: 700, color: "#F1F5F9" }}
                >
                  TOTAL
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  {totals.cantidad.toLocaleString("es-CL")}
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  {CLP(totals.ingreso_sin_iva)}
                </TableCell>
                <TableCell align="right">
                  <Chip
                    label={`${totalCmvPct}%`}
                    size="small"
                    color={cmvColor(parseFloat(totalCmvPct))}
                    sx={{ fontSize: "0.65rem", height: 20 }}
                  />
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  {CLP(totals.cmv)}
                </TableCell>
                <TableCell
                  align="right"
                  sx={{ fontWeight: 700, color: "error.main" }}
                >
                  {totalComisionPct !== "—" ? `${totalComisionPct}%` : "—"}
                </TableCell>
                <TableCell
                  align="right"
                  sx={{ fontWeight: 700, color: "success.main" }}
                >
                  {totalMarPct}%
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  {CLP(totals.margen_sin_iva)}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </DialogContent>
    </Dialog>
  );
};

export default SalesTableModal;
