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
} from "@mui/material";
import PriceCheckIcon from "@mui/icons-material/PriceCheck";
import CloseIcon from "@mui/icons-material/Close";
import { CLP, fmtMonth, cmvColor } from "../utils/formatters";

const COLS = [
  { id: "Producto", label: "Producto", numeric: false },
  { id: "Categoría", label: "Categoría", numeric: false },
  { id: "cantidad", label: "Cant.", numeric: true },
  { id: "avg_precio", label: "Precio (c/IVA)", numeric: true },
  { id: "avg_iva", label: "IVA", numeric: true },
  { id: "avg_precio_neto", label: "Precio neto", numeric: true },
  { id: "avg_costo_neto", label: "Costo neto", numeric: true },
  { id: "pct_costo", label: "% Costo", numeric: true },
  { id: "margen_bruto", label: "Margen bruto", numeric: true },
  { id: "pct_margen_bruto", label: "% Margen", numeric: true },
];

const marginColor = (pct) =>
  pct >= 60 ? "success" : pct >= 40 ? "warning" : "error";

const ProductPricesModal = ({ open, onClose, data, month }) => {
  const [orderBy, setOrderBy] = useState("avg_precio_neto");
  const [order, setOrder] = useState("desc");

  const handleSort = (col) => {
    if (orderBy === col) setOrder((o) => (o === "asc" ? "desc" : "asc"));
    else {
      setOrderBy(col);
      setOrder("desc");
    }
  };

  const sorted = [...(data || [])].sort((a, b) => {
    const av = a[orderBy],
      bv = b[orderBy];
    if (typeof av === "string")
      return order === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
    return order === "asc" ? av - bv : bv - av;
  });

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
          <PriceCheckIcon color="primary" />
          <Typography variant="h6">
            Precios y Márgenes por Producto
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
                      onClick={() => handleSort(c.id)}
                      hideSortIcon={false}
                    >
                      {c.label}
                    </TableSortLabel>
                  </TableCell>
                ))}
                <TableCell>Canales</TableCell>
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
                  <TableCell align="right">{CLP(row.avg_precio)}</TableCell>
                  <TableCell align="right" sx={{ color: "text.secondary" }}>
                    {CLP(row.avg_iva)}
                  </TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>
                    {CLP(row.avg_precio_neto)}
                  </TableCell>
                  <TableCell align="right" sx={{ color: "warning.main" }}>
                    {CLP(row.avg_costo_neto)}
                  </TableCell>
                  <TableCell align="right">
                    <Chip
                      label={`${row.pct_costo}%`}
                      size="small"
                      color={cmvColor(row.pct_costo)}
                      sx={{ fontSize: "0.65rem", height: 20 }}
                    />
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{
                      color:
                        row.margen_bruto >= 0 ? "success.main" : "error.main",
                      fontWeight: 600,
                    }}
                  >
                    {CLP(row.margen_bruto)}
                  </TableCell>
                  <TableCell align="right">
                    <Chip
                      label={`${row.pct_margen_bruto}%`}
                      size="small"
                      color={marginColor(row.pct_margen_bruto)}
                      sx={{ fontSize: "0.65rem", height: 20 }}
                    />
                  </TableCell>
                  <TableCell>
                    {row.tiene_uber_eats && (
                      <Chip
                        label="Uber Eats"
                        size="small"
                        sx={{
                          fontSize: "0.6rem",
                          height: 18,
                          bgcolor: "#1C1C1C",
                          color: "#06B6D4",
                        }}
                      />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </DialogContent>
    </Dialog>
  );
};

export default ProductPricesModal;
