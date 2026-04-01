import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import {
  Box,
  Paper,
  Typography,
  Chip,
  Divider,
  CircularProgress,
  Alert,
  Collapse,
  IconButton,
  Tooltip,
} from "@mui/material";
import LightbulbOutlinedIcon from "@mui/icons-material/LightbulbOutlined";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import RefreshIcon from "@mui/icons-material/Refresh";
import AccessTimeIcon from "@mui/icons-material/AccessTime";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { CLP } from "../utils/formatters";

// ── Score explanation popover ─────────────────────────────────────────────────
const SCORE_EXPLANATION = `Puntuación compuesta (0–100) que combina tres factores:

• Margen bruto (50 %) — qué tanto queda después de ingredientes y comisión Uber Eats. Productos con margen ≥ 70 % son los más rentables para promocionar.

• Eficiencia de costo (30 %) — inverso del CMV: cuanto menor el costo en ingredientes, mayor el puntaje. Un CMV ≤ 20 % indica muy baja presión de costo.

• Volumen de ventas (20 %) — relativo al producto más vendido del período. Evita recomendar productos con margen excelente pero rotación casi nula.

Fórmula: score = margen% × 0.5 + (100 − cmv%) × 0.3 + volumen_relativo × 0.2

Verde ≥ 80 · Amarillo ≥ 65 · Gris < 65`;

// ── Helpers ───────────────────────────────────────────────────────────────────
const fmt12h = (h) => {
  if (h === 0) return "12 am";
  if (h < 12) return `${h} am`;
  if (h === 12) return "12 pm";
  return `${h - 12} pm`;
};

const scoreColor = (score) => {
  if (score >= 80) return "#22C55E";
  if (score >= 65) return "#FBBF24";
  return "#94A3B8";
};

// ── ProductCard ───────────────────────────────────────────────────────────────
const ProductCard = ({ rank, item, accent }) => (
  <Box
    sx={{
      display: "flex",
      gap: 1.5,
      p: 1.5,
      borderRadius: 2,
      bgcolor: "#0F172A",
      border: `1px solid ${accent}30`,
      alignItems: "flex-start",
    }}
  >
    <Box
      sx={{
        minWidth: 28,
        height: 28,
        borderRadius: "50%",
        bgcolor: accent + "20",
        border: `1.5px solid ${accent}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      <Typography
        variant="caption"
        fontWeight={700}
        sx={{ color: accent, fontSize: "0.7rem" }}
      >
        {rank}
      </Typography>
    </Box>
    <Box sx={{ minWidth: 0, flex: 1 }}>
      <Typography
        variant="body2"
        fontWeight={600}
        sx={{ lineHeight: 1.3, mb: 0.5, whiteSpace: "normal" }}
      >
        {item.Producto}
      </Typography>
      <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mb: 0.75 }}>
        <Chip
          label={`Margen ${item.margen_pct}%`}
          size="small"
          sx={{
            fontSize: "0.6rem",
            height: 18,
            bgcolor: item.margen_pct >= 70 ? "#22C55E20" : "#FBBF2420",
            color: item.margen_pct >= 70 ? "#22C55E" : "#FBBF24",
            border: `1px solid ${item.margen_pct >= 70 ? "#22C55E40" : "#FBBF2440"}`,
          }}
        />
        <Chip
          label={`CMV ${item.cmv_pct}%`}
          size="small"
          sx={{
            fontSize: "0.6rem",
            height: 18,
            bgcolor: "#94A3B820",
            color: "#94A3B8",
          }}
        />
        <Chip
          label={CLP((item.ingreso_sin_iva / (item.cantidad || 1)) * 1.19)}
          size="small"
          sx={{
            fontSize: "0.6rem",
            height: 18,
            bgcolor: "#33415520",
            color: "#94A3B8",
          }}
        />
      </Box>
      <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
        {item.razones.map((r, i) => (
          <Typography
            key={i}
            variant="caption"
            sx={{ color: "#64748B", fontSize: "0.65rem" }}
          >
            {i > 0 ? "· " : ""}
            {r}
          </Typography>
        ))}
      </Box>
    </Box>
    <Box sx={{ textAlign: "right", flexShrink: 0 }}>
      <Typography
        variant="caption"
        fontWeight={700}
        sx={{ color: scoreColor(item.score), fontSize: "0.75rem" }}
      >
        {item.score}
      </Typography>
      <Typography
        variant="caption"
        sx={{ color: "#475569", display: "block", fontSize: "0.6rem" }}
      >
        score
      </Typography>
    </Box>
  </Box>
);

// ── HourBar ───────────────────────────────────────────────────────────────────
const HourBar = ({ hour, count, peak, highlight }) => {
  const pct = peak > 0 ? (count / peak) * 100 : 0;
  const color =
    highlight === "best"
      ? "#F97316"
      : highlight === "slow"
        ? "#38BDF8"
        : "#334155";
  return (
    <Tooltip title={`${fmt12h(hour)}: ${count} uds`} arrow>
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 0.25,
          cursor: "default",
        }}
      >
        <Box
          sx={{
            width: 18,
            height: 48,
            bgcolor: "#1E293B",
            borderRadius: 1,
            position: "relative",
            overflow: "hidden",
          }}
        >
          <Box
            sx={{
              position: "absolute",
              bottom: 0,
              left: 0,
              right: 0,
              height: `${pct}%`,
              bgcolor: color,
              transition: "height .4s ease",
            }}
          />
        </Box>
        <Typography
          variant="caption"
          sx={{
            fontSize: "0.55rem",
            color: highlight ? color : "#475569",
            fontWeight: highlight ? 700 : 400,
          }}
        >
          {hour}h
        </Typography>
      </Box>
    </Tooltip>
  );
};

// ── Main component ────────────────────────────────────────────────────────────
const PromotionAdvisor = ({ salesLoaded, selectedMonth }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params =
        selectedMonth && selectedMonth !== "all"
          ? { month: selectedMonth }
          : {};
      const res = await axios.get("/api/advisor/promotions/", { params });
      setData(res.data);
    } catch (e) {
      setError(e.response?.data?.error || "Error al cargar recomendaciones");
    } finally {
      setLoading(false);
    }
  }, [selectedMonth]);

  useEffect(() => {
    if (salesLoaded) fetch();
  }, [salesLoaded, fetch]);

  if (!salesLoaded) return null;

  const bestSet = new Set(data?.best_hours ?? []);
  const slowSet = new Set(data?.slow_hours ?? []);
  const peak = data
    ? Math.max(...Object.values(data.uber_hours).map((v) => v.count), 1)
    : 1;

  const ticketDelta =
    data?.avg_ticket_local > 0
      ? Math.round(
          ((data.avg_ticket_uber - data.avg_ticket_local) /
            data.avg_ticket_local) *
            100,
        )
      : null;

  return (
    <Paper
      elevation={0}
      sx={{ mt: 4, border: "1px solid #334155", overflow: "hidden" }}
    >
      {/* Header */}
      <Box
        sx={{
          px: 3,
          py: 1.5,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          bgcolor: "#0F172A",
          borderBottom: open ? "1px solid #1E293B" : "none",
          cursor: "pointer",
        }}
        onClick={() => setOpen((v) => !v)}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <LightbulbOutlinedIcon sx={{ color: "#FBBF24", fontSize: 20 }} />
          <Typography variant="h6" fontWeight={700} sx={{ fontSize: "1rem" }}>
            Recomendaciones para Promociones Uber Eats
          </Typography>
          {data && (
            <Chip
              label={`${data.uber_pct_of_units}% de ventas · ${data.uber_units} uds`}
              size="small"
              sx={{
                fontSize: "0.65rem",
                height: 18,
                bgcolor: "#1C1C1C",
                color: "#06B6D4",
              }}
            />
          )}
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          <Tooltip
            title={
              <Box
                sx={{
                  whiteSpace: "pre-line",
                  fontSize: "0.75rem",
                  lineHeight: 1.6,
                }}
              >
                {SCORE_EXPLANATION}
              </Box>
            }
            arrow
            placement="left"
            componentsProps={{
              tooltip: {
                sx: {
                  maxWidth: 360,
                  bgcolor: "#1E293B",
                  border: "1px solid #334155",
                },
              },
            }}
          >
            <IconButton
              size="small"
              onClick={(e) => e.stopPropagation()}
              sx={{ color: "#64748B" }}
            >
              <InfoOutlinedIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Actualizar recomendaciones">
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                fetch();
              }}
              sx={{ color: "text.secondary" }}
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <IconButton size="small" sx={{ color: "text.secondary" }}>
            {open ? (
              <ExpandLessIcon fontSize="small" />
            ) : (
              <ExpandMoreIcon fontSize="small" />
            )}
          </IconButton>
        </Box>
      </Box>

      <Collapse in={open}>
        {loading && (
          <Box sx={{ display: "flex", justifyContent: "center", py: 5 }}>
            <CircularProgress size={28} color="primary" />
          </Box>
        )}
        {error && (
          <Alert severity="error" sx={{ m: 2 }}>
            {error}
          </Alert>
        )}
        {!loading && data && (
          <Box sx={{ p: 3 }}>
            {/* ── Ticket comparison ── */}
            <Box
              sx={{
                display: "flex",
                gap: 3,
                mb: 3,
                p: 2,
                bgcolor: "#0F172A",
                borderRadius: 2,
                flexWrap: "wrap",
                alignItems: "center",
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <TrendingUpIcon sx={{ color: "#06B6D4", fontSize: 18 }} />
                <Typography variant="body2" color="text.secondary">
                  Ticket prom. Uber Eats:
                </Typography>
                <Typography
                  variant="body2"
                  fontWeight={700}
                  sx={{ color: "#06B6D4" }}
                >
                  {CLP(data.avg_ticket_uber)}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Ticket prom. Local:
                </Typography>
                <Typography variant="body2" fontWeight={700}>
                  {CLP(data.avg_ticket_local)}
                </Typography>
              </Box>
              {ticketDelta !== null && (
                <Chip
                  label={`Uber Eats paga ${ticketDelta > 0 ? "+" : ""}${ticketDelta}% por pedido`}
                  size="small"
                  color={ticketDelta >= 0 ? "success" : "error"}
                  sx={{ fontSize: "0.7rem", height: 22 }}
                />
              )}
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ ml: "auto" }}
              >
                Objetivo: aumentar ticket promedio mediante bundles y combos
              </Typography>
            </Box>

            {/* ── Product picks ── */}
            <Box sx={{ display: "flex", gap: 3, mb: 3, flexWrap: "wrap" }}>
              {/* Especialidades */}
              <Box sx={{ flex: "1 1 300px", minWidth: 0 }}>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                    mb: 1.5,
                  }}
                >
                  <Typography variant="subtitle2" sx={{ color: "#F97316" }}>
                    🍕 Top Especialidades
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    — mejores para combos ancla
                  </Typography>
                </Box>
                <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                  {(data.especialidades || []).map((item, i) => (
                    <ProductCard
                      key={item.Producto}
                      rank={i + 1}
                      item={item}
                      accent="#F97316"
                    />
                  ))}
                  {(data.especialidades || []).length === 0 && (
                    <Typography variant="caption" color="text.secondary">
                      Sin datos suficientes para esta categoría.
                    </Typography>
                  )}
                </Box>
              </Box>

              <Divider
                orientation="vertical"
                flexItem
                sx={{ display: { xs: "none", md: "block" } }}
              />

              {/* Extras */}
              <Box sx={{ flex: "1 1 300px", minWidth: 0 }}>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                    mb: 1.5,
                  }}
                >
                  <Typography variant="subtitle2" sx={{ color: "#38BDF8" }}>
                    🧃 Top Extras
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    — ideales para aumentar ticket
                  </Typography>
                </Box>
                <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                  {(data.extras || []).map((item, i) => (
                    <ProductCard
                      key={item.Producto}
                      rank={i + 1}
                      item={item}
                      accent="#38BDF8"
                    />
                  ))}
                  {(data.extras || []).length === 0 && (
                    <Typography variant="caption" color="text.secondary">
                      Sin datos suficientes para esta categoría.
                    </Typography>
                  )}
                </Box>
              </Box>
            </Box>

            {/* ── Timing ── */}
            <Divider sx={{ mb: 2.5 }} />
            <Box
              sx={{
                display: "flex",
                alignItems: "flex-start",
                gap: 1,
                mb: 1.5,
              }}
            >
              <AccessTimeIcon
                sx={{ color: "#FBBF24", fontSize: 18, mt: 0.2 }}
              />
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 0.25 }}>
                  Actividad Uber Eats por hora
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  <span style={{ color: "#F97316", fontWeight: 700 }}>■</span>{" "}
                  Horas pico &nbsp;
                  <span style={{ color: "#38BDF8", fontWeight: 700 }}>
                    ■
                  </span>{" "}
                  Oportunidad de promo
                  {data.best_weekday && (
                    <>
                      {" "}
                      &nbsp;·&nbsp; Mejor día:{" "}
                      <strong style={{ color: "#F1F5F9" }}>
                        {data.best_weekday}
                      </strong>
                    </>
                  )}
                </Typography>
              </Box>
            </Box>
            <Box
              sx={{
                display: "flex",
                gap: 0.5,
                flexWrap: "wrap",
                alignItems: "flex-end",
              }}
            >
              {Object.entries(data.uber_hours)
                .filter(([, v]) => v.count > 0)
                .map(([h, v]) => {
                  const hour = parseInt(h);
                  const highlight = bestSet.has(hour)
                    ? "best"
                    : slowSet.has(hour)
                      ? "slow"
                      : null;
                  return (
                    <HourBar
                      key={h}
                      hour={hour}
                      count={v.count}
                      peak={peak}
                      highlight={highlight}
                    />
                  );
                })}
            </Box>
            <Box sx={{ display: "flex", gap: 2, mt: 1.5, flexWrap: "wrap" }}>
              {data.best_hours.length > 0 && (
                <Typography variant="caption" color="text.secondary">
                  Pico:{" "}
                  <strong style={{ color: "#F97316" }}>
                    {data.best_hours.map(fmt12h).join(", ")}
                  </strong>{" "}
                  — promos flash aquí maximizan alcance
                </Typography>
              )}
              {data.slow_hours.length > 0 && (
                <Typography variant="caption" color="text.secondary">
                  Oportunidad:{" "}
                  <strong style={{ color: "#38BDF8" }}>
                    {data.slow_hours.map(fmt12h).join(", ")}
                  </strong>{" "}
                  — promos para llenar capacidad ociosa
                </Typography>
              )}
            </Box>
          </Box>
        )}
      </Collapse>
    </Paper>
  );
};

export default PromotionAdvisor;
