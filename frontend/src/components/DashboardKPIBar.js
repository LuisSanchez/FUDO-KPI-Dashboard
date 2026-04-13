import React from "react";
import { Box, Paper, Typography, Tooltip } from "@mui/material";
import { CLP } from "../utils/formatters";

// ── Color helpers ─────────────────────────────────────────────────────────────
const ebitdaColor = (pct) => {
  if (pct >= 25) return "#22C55E";
  if (pct >= 0) return "#F97316";
  return "#EF4444";
};

const cmvColor = (pct) => {
  if (pct <= 35) return "#22C55E";
  if (pct <= 45) return "#F97316";
  return "#EF4444";
};

const marginColor = (pct) => {
  if (pct >= 50) return "#22C55E";
  if (pct >= 30) return "#F97316";
  return "#EF4444";
};

// ── Single KPI tile ───────────────────────────────────────────────────────────
const Tile = ({ label, value, sub, valueColor, tooltip }) => {
  const content = (
    <Paper
      elevation={0}
      sx={{
        flex: "1 1 0",
        minWidth: { xs: "calc(50% - 6px)", sm: "calc(25% - 9px)", lg: 0 },
        p: { xs: 1.5, sm: 2 },
        border: "1px solid",
        borderColor: "divider",
        display: "flex",
        flexDirection: "column",
        gap: 0.3,
        cursor: tooltip ? "help" : "default",
      }}
    >
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{
          fontSize: "0.66rem",
          textTransform: "uppercase",
          letterSpacing: 0.6,
          lineHeight: 1.2,
        }}
      >
        {label}
      </Typography>
      <Typography
        fontWeight={700}
        sx={{
          color: valueColor ?? "text.primary",
          lineHeight: 1.15,
          fontSize: { xs: "1rem", sm: "1.1rem", md: "1.2rem" },
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
      >
        {value}
      </Typography>
      {sub && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ lineHeight: 1.2, fontSize: "0.68rem" }}
        >
          {sub}
        </Typography>
      )}
    </Paper>
  );

  return tooltip ? (
    <Tooltip title={tooltip} arrow placement="bottom">
      {content}
    </Tooltip>
  ) : (
    content
  );
};

// ── Main bar ──────────────────────────────────────────────────────────────────
const DashboardKPIBar = ({ results }) => {
  if (!results?.dashboard) return null;

  const ing = results.ingresos;
  const ebt = results.ebitda;
  const dash = results.dashboard;

  const ebitdaSign = ebt.ebitda_percentage >= 0 ? "+" : "";

  const tiles = [
    {
      label: "CMV",
      value: `${ing.cmv_percentage.toFixed(1)}%`,
      sub: `${CLP(ing.cmv)} en ingredientes`,
      valueColor: cmvColor(ing.cmv_percentage),
      tooltip:
        "Costo de Mercadería Vendida como % de ingresos s/IVA. Meta: 25–35%",
    },
    {
      label: "EBITDA",
      value: `${ebitdaSign}${ebt.ebitda_percentage.toFixed(1)}%`,
      sub: CLP(ebt.ebitda),
      valueColor: ebitdaColor(ebt.ebitda_percentage),
      tooltip: "Ingresos s/IVA − gastos operacionales. Meta: ≥ 25%",
    },
    {
      label: "Pizza promedio",
      value: CLP(dash.avg_precio_especialidades),
      sub: "s/IVA · Especialidades",
      tooltip: "Precio promedio por unidad de Especialidades, sin IVA",
    },
    {
      label: "Mejor día",
      value: dash.best_weekday?.label ?? "—",
      sub: dash.best_weekday
        ? `${dash.best_weekday.count.toLocaleString("es-CL")} uds. acumuladas`
        : "",
      tooltip: "Día de la semana con mayor volumen de ventas en el período",
    },
    {
      label: "Mejor hora",
      value: dash.best_hour?.label ?? "—",
      sub: dash.best_hour
        ? `${dash.best_hour.count.toLocaleString("es-CL")} uds. acumuladas`
        : "",
      tooltip: "Hora del día con mayor volumen de ventas en el período",
    },
    {
      label: "Top Especialidad",
      value: dash.top_especialidad?.producto ?? "—",
      sub: dash.top_especialidad
        ? `${dash.top_especialidad.cantidad.toLocaleString("es-CL")} unidades`
        : "",
      tooltip: "Especialidad más vendida por unidades en el período",
    },
    {
      label: "Margen Local",
      value: `${dash.local_margin_pct.toFixed(1)}%`,
      sub: "s/IVA sobre ingreso",
      valueColor: marginColor(dash.local_margin_pct),
      tooltip:
        "Margen neto del canal presencial: (Ingreso − Ingredientes) / Ingreso, sin IVA",
    },
    {
      label: "Margen Uber",
      value: `${dash.uber_margin_pct.toFixed(1)}%`,
      sub: "s/IVA · neto comisión 25%",
      valueColor: marginColor(dash.uber_margin_pct),
      tooltip:
        "Margen neto del canal Uber Eats: (Ingreso − Ingredientes − Comisión 25%) / Ingreso, sin IVA",
    },
  ];

  return (
    <Box
      sx={{
        display: "flex",
        flexWrap: "wrap",
        gap: { xs: 1, sm: 1.5 },
        mb: 3,
      }}
    >
      {tiles.map((t) => (
        <Tile key={t.label} {...t} />
      ))}
    </Box>
  );
};

export default DashboardKPIBar;
