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
} from "@mui/material";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import CloseIcon from "@mui/icons-material/Close";
import { CLP, fmtMonth, TIPO_COLOR } from "../utils/formatters";

const ExpensesTableModal = ({ open, onClose, data, month }) => {
  const [filter, setFilter] = useState("all");

  const filtered = (data || []).filter(
    (r) => filter === "all" || r.Tipo === filter,
  );
  const total = filtered.reduce((s, r) => s + r.Importe, 0);

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
          <ReceiptLongIcon color="primary" />
          <Typography variant="h6">
            Gastos{month && month !== "all" ? ` — ${fmtMonth(month)}` : ""}
          </Typography>
          <Chip
            label={`${filtered.length} registros`}
            size="small"
            variant="outlined"
          />
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>
      <DialogContent sx={{ p: 0 }}>
        <Box sx={{ px: 2, pt: 2, pb: 1, display: "flex", gap: 1 }}>
          {["all", "Operacional", "Préstamo", "Activo Fijo"].map((t) => (
            <Chip
              key={t}
              label={t === "all" ? "Todos" : t}
              size="small"
              onClick={() => setFilter(t)}
              variant={filter === t ? "filled" : "outlined"}
              color={filter === t ? "primary" : "default"}
              sx={{ cursor: "pointer" }}
            />
          ))}
          <Box sx={{ ml: "auto" }}>
            <Typography variant="body2" fontWeight={600}>
              Total: {CLP(total)}
            </Typography>
          </Box>
        </Box>
        <TableContainer sx={{ maxHeight: "65vh" }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                {[
                  "Fecha",
                  "Proveedor",
                  "Categoría",
                  "Subcategoría",
                  "Comentario",
                  "Importe",
                  "Estado",
                  "Tipo",
                ].map((h) => (
                  <TableCell key={h} align={h === "Importe" ? "right" : "left"}>
                    {h}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {filtered.map((row, i) => (
                <TableRow
                  key={i}
                  hover
                  sx={{ "&:hover": { bgcolor: "#ffffff08" } }}
                >
                  <TableCell
                    sx={{ whiteSpace: "nowrap", color: "text.secondary" }}
                  >
                    {row.Fecha}
                  </TableCell>
                  <TableCell sx={{ fontWeight: 500, maxWidth: 180 }}>
                    {row.Proveedor}
                  </TableCell>
                  <TableCell>{row.Categoría}</TableCell>
                  <TableCell
                    sx={{ color: "text.secondary", fontSize: "0.8rem" }}
                  >
                    {row.Subcategoría || "—"}
                  </TableCell>
                  <TableCell
                    sx={{
                      color: "text.secondary",
                      fontSize: "0.8rem",
                      maxWidth: 200,
                    }}
                  >
                    {row.Comentario || "—"}
                  </TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>
                    {CLP(row.Importe)}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={row["Estado del pago"]}
                      size="small"
                      color={
                        row["Estado del pago"] === "Pagado"
                          ? "success"
                          : "warning"
                      }
                      sx={{ fontSize: "0.65rem", height: 20 }}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={row.Tipo}
                      size="small"
                      color={TIPO_COLOR[row.Tipo] || "default"}
                      sx={{ fontSize: "0.65rem", height: 20 }}
                    />
                  </TableCell>
                </TableRow>
              ))}
              <TableRow
                sx={{ bgcolor: "#0F172A", position: "sticky", bottom: 0 }}
              >
                <TableCell colSpan={5} sx={{ fontWeight: 700 }}>
                  TOTAL
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>
                  {CLP(total)}
                </TableCell>
                <TableCell colSpan={2} />
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </DialogContent>
    </Dialog>
  );
};

export default ExpensesTableModal;
