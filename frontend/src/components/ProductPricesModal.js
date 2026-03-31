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
  TextField,
  InputAdornment,
} from "@mui/material";
import PriceCheckIcon from "@mui/icons-material/PriceCheck";
import CloseIcon from "@mui/icons-material/Close";
import SearchIcon from "@mui/icons-material/Search";
import { CLP, fmtMonth, cmvColor } from "../utils/formatters";

const COLS = [
  { id: "Producto", label: "Producto", numeric: false },
  { id: "Categoría", label: "Categoría", numeric: false },
  { id: "cantidad", label: "Cant.", numeric: true },
  { id: "avg_precio", label: "Precio (c/IVA)", numeric: true },
  { id: "avg_precio_uber_eats", label: "Precio Uber Eats", numeric: true },
  { id: "avg_iva", label: "IVA", numeric: true },
  { id: "avg_precio_neto", label: "Precio neto", numeric: true },
  { id: "avg_costo_neto", label: "Costo neto", numeric: true },
  { id: "pct_costo", label: "% Costo", numeric: true },
  { id: "margen_bruto", label: "Margen bruto", numeric: true },
  { id: "pct_margen_bruto", label: "% Margen", numeric: true },
];

const marginColor = (pct) =>
  pct >= 60 ? "success" : pct >= 40 ? "warning" : "error";

const CHANNEL_FILTERS = [
  { key: "all", label: "Todos" },
  { key: "uber_eats", label: "Uber Eats" },
  { key: "local", label: "Solo local" },
];

const ProductPricesModal = ({ open, onClose, data, month }) => {
  const [orderBy, setOrderBy] = useState("avg_precio_neto");
  const [order, setOrder] = useState("desc");
  const [search, setSearch] = useState("");
  const [channel, setChannel] = useState("all");
  const [categoria, setCategoria] = useState("all");

  const categories = [
    "all",
    ...Array.from(new Set((data || []).map((r) => r.Categoría))).sort(),
  ];

  const handleSort = (col) => {
    if (orderBy === col) setOrder((o) => (o === "asc" ? "desc" : "asc"));
    else {
      setOrderBy(col);
      setOrder("desc");
    }
  };

  const q = search.trim().toLowerCase();
  const filtered = (data || []).filter((r) => {
    if (q && !r.Producto.toLowerCase().includes(q)) return false;
    if (channel === "uber_eats" && !r.tiene_uber_eats) return false;
    if (channel === "local" && r.tiene_uber_eats) return false;
    if (categoria !== "all" && r.Categoría !== categoria) return false;
    return true;
  });

  const sorted = [...filtered].sort((a, b) => {
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
            label={`${sorted.length} / ${(data || []).length} productos`}
            size="small"
            variant="outlined"
          />
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <TextField
            size="small"
            placeholder="Buscar producto…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ fontSize: 16, color: "text.secondary" }} />
                </InputAdornment>
              ),
            }}
            sx={{
              width: 200,
              "& .MuiOutlinedInput-root": { fontSize: "0.8rem" },
            }}
          />
          <IconButton onClick={onClose} size="small">
            <CloseIcon fontSize="small" />
          </IconButton>
        </Box>
      </DialogTitle>

      {/* Filters row */}
      <Box
        sx={{
          px: 2,
          pb: 1,
          display: "flex",
          alignItems: "center",
          gap: 2,
          flexWrap: "wrap",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Canal:
          </Typography>
          {CHANNEL_FILTERS.map((f) => (
            <Chip
              key={f.key}
              label={f.label}
              size="small"
              onClick={() => setChannel(f.key)}
              variant={channel === f.key ? "filled" : "outlined"}
              color={channel === f.key ? "primary" : "default"}
              sx={{ cursor: "pointer" }}
            />
          ))}
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Categoría:
          </Typography>
          {categories.map((cat) => (
            <Chip
              key={cat}
              label={cat === "all" ? "Todas" : cat}
              size="small"
              onClick={() => setCategoria(cat)}
              variant={categoria === cat ? "filled" : "outlined"}
              color={categoria === cat ? "primary" : "default"}
              sx={{ cursor: "pointer" }}
            />
          ))}
        </Box>
      </Box>

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
                  <TableCell align="right">{CLP(row.avg_precio)}</TableCell>
                  <TableCell align="right">
                    {row.avg_precio_uber_eats > 0 ? (
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "flex-end",
                          gap: 0.5,
                        }}
                      >
                        <Typography
                          variant="caption"
                          sx={{
                            fontWeight: 600,
                            color:
                              row.avg_precio_uber_eats !== row.avg_precio
                                ? "warning.main"
                                : "text.primary",
                          }}
                        >
                          {CLP(row.avg_precio_uber_eats)}
                        </Typography>
                        {row.avg_precio_uber_eats !== row.avg_precio && (
                          <Chip
                            label={`${row.avg_precio_uber_eats > row.avg_precio ? "+" : ""}${Math.round(row.avg_precio_uber_eats - row.avg_precio).toLocaleString("es-CL")}`}
                            size="small"
                            color={
                              row.avg_precio_uber_eats > row.avg_precio
                                ? "success"
                                : "error"
                            }
                            sx={{ fontSize: "0.6rem", height: 16 }}
                          />
                        )}
                      </Box>
                    ) : (
                      <Typography variant="caption" color="text.secondary">
                        —
                      </Typography>
                    )}
                  </TableCell>
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
