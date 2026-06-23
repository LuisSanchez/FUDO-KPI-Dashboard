import React, { useState, useMemo } from "react";
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
  Tooltip,
  ToggleButtonGroup,
  ToggleButton,
  Divider,
} from "@mui/material";
import TableChartIcon from "@mui/icons-material/TableChart";
import CloseIcon from "@mui/icons-material/Close";
import SearchIcon from "@mui/icons-material/Search";
import DeliveryDiningIcon from "@mui/icons-material/DeliveryDining";
import StorefrontIcon from "@mui/icons-material/Storefront";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import CompareArrowsIcon from "@mui/icons-material/CompareArrows";
import { CLP, fmtMonth, cmvColor } from "../utils/formatters";

// ── Constants ─────────────────────────────────────────────────────────────────
const CHANNEL_ORDER = ["Uber Eats", "Local"];

const CHANNEL_META = {
  "Uber Eats": {
    color: "#3B82F6",
    icon: <DeliveryDiningIcon sx={{ fontSize: 14 }} />,
  },
  Local: { color: "#22C55E", icon: <StorefrontIcon sx={{ fontSize: 14 }} /> },
};

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
  { id: "has_imputed_cost", label: "Costo imputado", numeric: false },
];

// ── Helpers ───────────────────────────────────────────────────────────────────
const pct = (num, denom) =>
  denom > 0 ? ((num / denom) * 100).toFixed(1) : "—";

const cmvHex = (p) => (p <= 35 ? "#22C55E" : p <= 45 ? "#F97316" : "#EF4444");
const margenHex = (p) =>
  p >= 50 ? "#22C55E" : p >= 30 ? "#F97316" : "#EF4444";

const sumTotals = (rows) =>
  rows.reduce(
    (acc, r) => ({
      cantidad: acc.cantidad + r.cantidad,
      ingreso_sin_iva: acc.ingreso_sin_iva + r.ingreso_sin_iva,
      cmv: acc.cmv + r.cmv,
      margen_sin_iva: acc.margen_sin_iva + r.margen_sin_iva,
      comision: acc.comision + r.comision,
    }),
    { cantidad: 0, ingreso_sin_iva: 0, cmv: 0, margen_sin_iva: 0, comision: 0 },
  );

// ── Product comparison dialog ─────────────────────────────────────────────────
const ProductComparisonDialog = ({ product, data, onClose }) => {
  if (!product) return null;

  const rows = (data || []).filter((r) => r.Producto === product);
  if (rows.length === 0) return null;

  const categoria = rows[0]?.Categoría ?? "";

  // Ordered channels present for this product
  const channels = [
    ...CHANNEL_ORDER.filter((ch) => rows.some((r) => r.canal === ch)),
    ...rows.map((r) => r.canal).filter((ch) => !CHANNEL_ORDER.includes(ch)),
  ].filter((ch, i, arr) => arr.indexOf(ch) === i);

  const getRow = (ch) => rows.find((r) => r.canal === ch);
  const totals = sumTotals(rows);
  const showTotal = channels.length > 1;

  // Derived totals
  const tCmvPct =
    totals.ingreso_sin_iva > 0
      ? (totals.cmv / totals.ingreso_sin_iva) * 100
      : 0;
  const tComPct =
    totals.ingreso_sin_iva > 0
      ? (totals.comision / 1.19 / totals.ingreso_sin_iva) * 100
      : 0;
  const tMarPct =
    totals.ingreso_sin_iva > 0
      ? (totals.margen_sin_iva / totals.ingreso_sin_iva) * 100
      : 0;
  const tPrecioUd =
    totals.cantidad > 0 ? totals.ingreso_sin_iva / totals.cantidad : 0;
  const tMargenUd =
    totals.cantidad > 0 ? totals.margen_sin_iva / totals.cantidad : 0;

  const metrics = [
    {
      label: "Unidades vendidas",
      get: (r) => r.cantidad.toLocaleString("es-CL"),
      total: totals.cantidad.toLocaleString("es-CL"),
    },
    {
      label: "Precio promedio s/IVA",
      get: (r) => (r.cantidad > 0 ? CLP(r.ingreso_sin_iva / r.cantidad) : "—"),
      total: CLP(tPrecioUd),
    },
    {
      label: "Precio promedio c/IVA",
      get: (r) =>
        r.cantidad > 0 ? CLP((r.ingreso_sin_iva / r.cantidad) * 1.19) : "—",
      total: CLP(tPrecioUd * 1.19),
    },
    { divider: true },
    {
      label: "Ingreso total s/IVA",
      bold: true,
      get: (r) => CLP(r.ingreso_sin_iva),
      total: CLP(totals.ingreso_sin_iva),
    },
    {
      label: "CMV%",
      get: (r) => `${r.cmv_pct.toFixed(1)}%`,
      color: (r) => cmvHex(r.cmv_pct),
      total: `${tCmvPct.toFixed(1)}%`,
      totalColor: cmvHex(tCmvPct),
    },
    {
      label: "CMV $",
      get: (r) => CLP(r.cmv),
      total: CLP(totals.cmv),
    },
    {
      label: "Comisión Uber%",
      get: (r) => (r.comision_pct > 0 ? `${r.comision_pct.toFixed(1)}%` : "—"),
      color: (r) => (r.comision_pct > 0 ? "#EF4444" : "#475569"),
      total: tComPct > 0 ? `${tComPct.toFixed(1)}%` : "—",
      totalColor: tComPct > 0 ? "#EF4444" : "#475569",
    },
    {
      label: "Comisión $ s/IVA",
      get: (r) => (r.comision > 0 ? CLP(r.comision / 1.19) : "—"),
      total: totals.comision > 0 ? CLP(totals.comision / 1.19) : "—",
    },
    { divider: true },
    {
      label: "Margen%",
      bold: true,
      get: (r) => `${r.margen_pct.toFixed(1)}%`,
      color: (r) => margenHex(r.margen_pct),
      total: `${tMarPct.toFixed(1)}%`,
      totalColor: margenHex(tMarPct),
    },
    {
      label: "Margen $ total",
      bold: true,
      get: (r) => CLP(r.margen_sin_iva),
      total: CLP(totals.margen_sin_iva),
    },
    {
      label: "Margen por unidad",
      get: (r) => (r.cantidad > 0 ? CLP(r.margen_sin_iva / r.cantidad) : "—"),
      total: CLP(tMargenUd),
    },
  ];

  return (
    <Dialog
      open={!!product}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{ sx: { border: "1px solid", borderColor: "divider" } }}
    >
      <DialogTitle
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          pb: 1,
        }}
      >
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
            <CompareArrowsIcon sx={{ color: "primary.main", fontSize: 20 }} />
            <Typography variant="h6" fontWeight={700} sx={{ lineHeight: 1.2 }}>
              {product}
            </Typography>
          </Box>
          <Chip
            label={categoria}
            size="small"
            sx={{ fontSize: "0.65rem", height: 18 }}
          />
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ bgcolor: "background.default" }}>
                <TableCell
                  sx={{
                    color: "text.secondary",
                    fontSize: "0.72rem",
                    width: "36%",
                  }}
                >
                  Métrica
                </TableCell>
                {channels.map((ch) => {
                  const meta = CHANNEL_META[ch] ?? {
                    color: "#94A3B8",
                    icon: null,
                  };
                  return (
                    <TableCell key={ch} align="right">
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "flex-end",
                          gap: 0.5,
                          color: meta.color,
                          fontWeight: 700,
                          fontSize: "0.8rem",
                        }}
                      >
                        {meta.icon}
                        {ch}
                      </Box>
                    </TableCell>
                  );
                })}
                {showTotal && (
                  <TableCell
                    align="right"
                    sx={{
                      color: "text.secondary",
                      fontWeight: 700,
                      fontSize: "0.72rem",
                    }}
                  >
                    Total
                  </TableCell>
                )}
              </TableRow>
            </TableHead>

            <TableBody>
              {metrics.map((m, i) => {
                if (m.divider) {
                  return (
                    <TableRow key={`div-${i}`}>
                      <TableCell
                        colSpan={channels.length + (showTotal ? 2 : 1)}
                        sx={{ py: 0, border: "none", bgcolor: "action.hover" }}
                      >
                        <Divider />
                      </TableCell>
                    </TableRow>
                  );
                }
                return (
                  <TableRow key={m.label} hover>
                    <TableCell
                      sx={{ color: "text.secondary", fontSize: "0.75rem" }}
                    >
                      {m.label}
                    </TableCell>
                    {channels.map((ch) => {
                      const row = getRow(ch);
                      const val = row ? m.get(row) : "—";
                      const color = row && m.color ? m.color(row) : undefined;
                      return (
                        <TableCell
                          key={ch}
                          align="right"
                          sx={{
                            fontWeight: m.bold ? 700 : 400,
                            color: color ?? "text.primary",
                            fontSize: "0.82rem",
                          }}
                        >
                          {val}
                        </TableCell>
                      );
                    })}
                    {showTotal && (
                      <TableCell
                        align="right"
                        sx={{
                          fontWeight: m.bold ? 700 : 500,
                          color: m.totalColor ?? "text.secondary",
                          fontSize: "0.82rem",
                          borderLeft: "1px solid",
                          borderLeftColor: "divider",
                        }}
                      >
                        {m.total}
                      </TableCell>
                    )}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </DialogContent>
    </Dialog>
  );
};

// ── Main table rows ───────────────────────────────────────────────────────────
const ProductRow = ({ row, onRowClick }) => (
  <TableRow
    hover
    onClick={() => onRowClick(row.Producto)}
    sx={{ cursor: "pointer" }}
  >
    <TableCell>
      <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
        <Typography
          variant="body2"
          fontWeight={500}
          sx={{
            "&:hover": { color: "primary.main" },
            transition: "color 0.15s",
          }}
        >
          {row.Producto}
        </Typography>
        <ChevronRightIcon
          sx={{
            fontSize: 14,
            color: "primary.main",
            opacity: 0,
            ".MuiTableRow-root:hover &": { opacity: 0.6 },
          }}
        />
      </Box>
    </TableCell>
    <TableCell>
      <Chip
        label={row.Categoría}
        size="small"
        sx={{ fontSize: "0.65rem", height: 18 }}
      />
    </TableCell>
    <TableCell align="right">{row.cantidad.toLocaleString("es-CL")}</TableCell>
    <TableCell align="right">{CLP(row.ingreso_sin_iva)}</TableCell>
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
          <Tooltip title="CMV 0%: este producto no tiene costo de ingredientes registrado en FUDO.">
            <Typography
              variant="caption"
              sx={{ color: "warning.main", fontWeight: 700, cursor: "help" }}
            >
              ⚠
            </Typography>
          </Tooltip>
        )}
        <Chip
          label={`${row.cmv_pct}%`}
          size="small"
          color={row.cmv_pct === 0 ? "warning" : cmvColor(row.cmv_pct)}
          sx={{ fontSize: "0.65rem", height: 20 }}
        />
      </Box>
    </TableCell>
    <TableCell align="right">{CLP(row.cmv)}</TableCell>
    <TableCell align="right">
      <Typography
        variant="caption"
        sx={{
          color: row.comision_pct > 0 ? "error.main" : "text.secondary",
          fontWeight: row.comision_pct > 0 ? 600 : 400,
        }}
      >
        {row.comision_pct > 0 ? `${row.comision_pct}%` : "—"}
      </Typography>
    </TableCell>
    <TableCell align="right">
      <Typography
        variant="caption"
        sx={{ color: margenHex(row.margen_pct), fontWeight: 600 }}
      >
        {row.margen_pct}%
      </Typography>
    </TableCell>
    <TableCell align="right">{CLP(row.margen_sin_iva)}</TableCell>
    <TableCell align="center">
      {row.has_imputed_cost ? (
        <Tooltip
          title={`${row.cost_imputed_rows || "Algunas"} filas tenían Costo base = 0 en FUDO y se imputó desde el mismo producto en el período.`}
        >
          <Chip
            label="Sí"
            size="small"
            color="warning"
            variant="outlined"
            sx={{ fontSize: "0.65rem", height: 20 }}
          />
        </Tooltip>
      ) : (
        <Typography variant="caption" color="text.disabled">
          —
        </Typography>
      )}
    </TableCell>
  </TableRow>
);

const SectionHeader = ({ canal }) => {
  const meta = CHANNEL_META[canal] ?? { color: "#94A3B8", icon: null };
  return (
    <TableRow>
      <TableCell
        colSpan={COLS.length}
        sx={{
          bgcolor: "background.default",
          py: 0.75,
          borderBottom: `2px solid ${meta.color}30`,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
          <Box
            sx={{ color: meta.color, display: "flex", alignItems: "center" }}
          >
            {meta.icon}
          </Box>
          <Typography
            variant="caption"
            sx={{
              color: meta.color,
              fontWeight: 700,
              fontSize: "0.72rem",
              letterSpacing: 0.5,
            }}
          >
            {canal.toUpperCase()}
          </Typography>
        </Box>
      </TableCell>
    </TableRow>
  );
};

const SubtotalRow = ({ rows, label, color }) => {
  const t = sumTotals(rows);
  const cmvP = pct(t.cmv, t.ingreso_sin_iva);
  const comP = pct(t.comision / 1.19, t.ingreso_sin_iva);
  const marP = pct(t.margen_sin_iva, t.ingreso_sin_iva);
  return (
    <TableRow sx={{ bgcolor: "action.hover" }}>
      <TableCell
        colSpan={2}
        sx={{
          fontWeight: 600,
          color: color ?? "text.secondary",
          fontSize: "0.7rem",
          py: 0.5,
        }}
      >
        {label}
      </TableCell>
      <TableCell
        align="right"
        sx={{ fontWeight: 600, py: 0.5, fontSize: "0.75rem" }}
      >
        {t.cantidad.toLocaleString("es-CL")}
      </TableCell>
      <TableCell
        align="right"
        sx={{ fontWeight: 600, py: 0.5, fontSize: "0.75rem" }}
      >
        {CLP(t.ingreso_sin_iva)}
      </TableCell>
      <TableCell align="right" sx={{ py: 0.5 }}>
        <Chip
          label={`${cmvP}%`}
          size="small"
          color={cmvColor(parseFloat(cmvP))}
          sx={{ fontSize: "0.6rem", height: 18 }}
        />
      </TableCell>
      <TableCell
        align="right"
        sx={{ fontWeight: 600, py: 0.5, fontSize: "0.75rem" }}
      >
        {CLP(t.cmv)}
      </TableCell>
      <TableCell
        align="right"
        sx={{
          fontWeight: 600,
          py: 0.5,
          color: "error.main",
          fontSize: "0.75rem",
        }}
      >
        {comP !== "—" ? `${comP}%` : "—"}
      </TableCell>
      <TableCell
        align="right"
        sx={{
          fontWeight: 600,
          py: 0.5,
          color: "success.main",
          fontSize: "0.75rem",
        }}
      >
        {marP}%
      </TableCell>
      <TableCell
        align="right"
        sx={{ fontWeight: 600, py: 0.5, fontSize: "0.75rem" }}
      >
        {CLP(t.margen_sin_iva)}
      </TableCell>
    </TableRow>
  );
};

const GrandTotalRow = ({ rows }) => {
  const t = sumTotals(rows);
  const cmvP = pct(t.cmv, t.ingreso_sin_iva);
  const comP = pct(t.comision / 1.19, t.ingreso_sin_iva);
  const marP = pct(t.margen_sin_iva, t.ingreso_sin_iva);
  return (
    <TableRow
      sx={{ bgcolor: "background.default", position: "sticky", bottom: 0 }}
    >
      <TableCell colSpan={2} sx={{ fontWeight: 700, color: "text.primary" }}>
        TOTAL
      </TableCell>
      <TableCell align="right" sx={{ fontWeight: 700 }}>
        {t.cantidad.toLocaleString("es-CL")}
      </TableCell>
      <TableCell align="right" sx={{ fontWeight: 700 }}>
        {CLP(t.ingreso_sin_iva)}
      </TableCell>
      <TableCell align="right">
        <Chip
          label={`${cmvP}%`}
          size="small"
          color={cmvColor(parseFloat(cmvP))}
          sx={{ fontSize: "0.65rem", height: 20 }}
        />
      </TableCell>
      <TableCell align="right" sx={{ fontWeight: 700 }}>
        {CLP(t.cmv)}
      </TableCell>
      <TableCell align="right" sx={{ fontWeight: 700, color: "error.main" }}>
        {comP !== "—" ? `${comP}%` : "—"}
      </TableCell>
      <TableCell align="right" sx={{ fontWeight: 700, color: "success.main" }}>
        {marP}%
      </TableCell>
      <TableCell align="right" sx={{ fontWeight: 700 }}>
        {CLP(t.margen_sin_iva)}
      </TableCell>
    </TableRow>
  );
};

// ── Main modal ────────────────────────────────────────────────────────────────
const SalesTableModal = ({ open, onClose, data, month }) => {
  const [orderBy, setOrderBy] = useState("ingreso_sin_iva");
  const [order, setOrder] = useState("desc");
  const [search, setSearch] = useState("");
  const [channelFilter, setChannelFilter] = useState("all");
  const [clickedProduct, setClickedProduct] = useState(null);

  const handleSort = (col) => {
    if (orderBy === col) setOrder((o) => (o === "asc" ? "desc" : "asc"));
    else {
      setOrderBy(col);
      setOrder("desc");
    }
  };

  const availableChannels = useMemo(
    () =>
      CHANNEL_ORDER.filter((ch) => (data || []).some((r) => r.canal === ch)),
    [data],
  );

  const q = search.trim().toLowerCase();
  const filtered = useMemo(
    () =>
      (data || []).filter((r) => {
        const matchSearch =
          !q ||
          r.Producto.toLowerCase().includes(q) ||
          r.Categoría.toLowerCase().includes(q);
        const matchChannel =
          channelFilter === "all" || r.canal === channelFilter;
        return matchSearch && matchChannel;
      }),
    [data, q, channelFilter],
  );

  const sorted = useMemo(
    () =>
      [...filtered].sort((a, b) => {
        const av = a[orderBy],
          bv = b[orderBy];
        if (typeof av === "string")
          return order === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
        return order === "asc" ? av - bv : bv - av;
      }),
    [filtered, orderBy, order],
  );

  const groups = useMemo(() => {
    // Single O(n) pass: bucket rows by channel
    const buckets = {};
    for (const r of sorted) {
      const key = CHANNEL_ORDER.includes(r.canal) ? r.canal : "__other__";
      (buckets[key] ??= []).push(r);
    }
    const known = CHANNEL_ORDER.filter((ch) => buckets[ch]?.length).map(
      (ch) => ({ canal: ch, rows: buckets[ch] }),
    );
    if (buckets["__other__"]?.length)
      known.push({ canal: "Otros", rows: buckets["__other__"] });
    return known;
  }, [sorted]);

  const uniqueProducts = useMemo(
    () => new Set(filtered.map((r) => r.Producto)).size,
    [filtered],
  );

  return (
    <>
      <Dialog
        open={open}
        onClose={onClose}
        maxWidth="xl"
        fullWidth
        PaperProps={{
          sx: {
            border: "1px solid",
            borderColor: "divider",
            maxHeight: "90vh",
          },
        }}
      >
        <DialogTitle
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 1,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <TableChartIcon color="primary" />
            <Typography variant="h6">
              Ventas por Producto
              {month && month !== "all" ? ` — ${fmtMonth(month)}` : ""}
            </Typography>
            <Chip
              label={`${uniqueProducts} productos`}
              size="small"
              variant="outlined"
            />
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ ml: 0.5 }}
            >
              · Click en un producto para comparar canales
            </Typography>
          </Box>

          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              flexWrap: "wrap",
            }}
          >
            <ToggleButtonGroup
              value={channelFilter}
              exclusive
              onChange={(_, v) => v && setChannelFilter(v)}
              size="small"
            >
              <ToggleButton
                value="all"
                sx={{ fontSize: "0.7rem", px: 1.5, py: 0.5 }}
              >
                Todos
              </ToggleButton>
              {availableChannels.map((ch) => {
                const meta = CHANNEL_META[ch] ?? {};
                return (
                  <ToggleButton
                    key={ch}
                    value={ch}
                    sx={{ fontSize: "0.7rem", px: 1.5, py: 0.5, gap: 0.5 }}
                  >
                    <Box
                      sx={{
                        color: meta.color,
                        display: "flex",
                        alignItems: "center",
                      }}
                    >
                      {meta.icon}
                    </Box>
                    {ch}
                  </ToggleButton>
                );
              })}
            </ToggleButtonGroup>

            <TextField
              size="small"
              placeholder="Buscar producto o categoría…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon
                      sx={{ fontSize: 16, color: "text.secondary" }}
                    />
                  </InputAdornment>
                ),
              }}
              sx={{
                width: 220,
                "& .MuiOutlinedInput-root": { fontSize: "0.8rem" },
              }}
            />
            <IconButton onClick={onClose} size="small">
              <CloseIcon fontSize="small" />
            </IconButton>
          </Box>
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
                      >
                        {c.label}
                      </TableSortLabel>
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>

              <TableBody>
                {channelFilter === "all"
                  ? groups.map(({ canal, rows }) => (
                      <React.Fragment key={canal}>
                        <SectionHeader canal={canal} />
                        {rows.map((row, i) => (
                          <ProductRow
                            key={`${canal}-${i}`}
                            row={row}
                            onRowClick={setClickedProduct}
                          />
                        ))}
                        <SubtotalRow
                          rows={rows}
                          label={`Subtotal ${canal}`}
                          color={CHANNEL_META[canal]?.color}
                        />
                      </React.Fragment>
                    ))
                  : sorted.map((row, i) => (
                      <ProductRow
                        key={i}
                        row={row}
                        onRowClick={setClickedProduct}
                      />
                    ))}
                <GrandTotalRow rows={sorted} />
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
      </Dialog>

      {/* Product comparison dialog — stacks on top of the sales table */}
      <ProductComparisonDialog
        product={clickedProduct}
        data={data}
        onClose={() => setClickedProduct(null)}
      />
    </>
  );
};

export default SalesTableModal;
