import React, { useState, useCallback, useEffect, useMemo } from "react";
import axios from "axios";
import {
  Box,
  Paper,
  Typography,
  Autocomplete,
  TextField,
  CircularProgress,
  Chip,
  Divider,
  Alert,
  InputAdornment,
} from "@mui/material";
import BalanceIcon from "@mui/icons-material/Balance";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import CalculateIcon from "@mui/icons-material/Calculate";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import TimerIcon from "@mui/icons-material/Timer";

// ── Helpers ───────────────────────────────────────────────────────────────────
const CLP = (v) =>
  new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    minimumFractionDigits: 0,
  }).format(v);

const ebitdaHex = (pct) =>
  pct >= 25 ? "#22C55E" : pct >= 0 ? "#FBBF24" : "#EF4444";

/** Days elapsed and remaining in the current calendar month */
function getMonthDays() {
  const today = new Date();
  const elapsed = today.getDate(); // 1-based day of month
  const totalDays = new Date(
    today.getFullYear(),
    today.getMonth() + 1,
    0,
  ).getDate();
  const remaining = totalDays - elapsed;
  return { elapsed, remaining, totalDays };
}

// ── TargetCard ────────────────────────────────────────────────────────────────
const TargetCard = ({
  icon,
  title,
  alreadyMet,
  impossible,
  totalUnits,
  currentUnits,
  additionalUnits,
  accentColor,
  daysElapsed,
  daysRemaining,
}) => {
  const currentRate =
    daysElapsed > 0 && currentUnits != null
      ? (currentUnits / daysElapsed).toFixed(1)
      : null;
  const neededRate =
    daysRemaining > 0 && additionalUnits != null
      ? (additionalUnits / daysRemaining).toFixed(1)
      : null;

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2.5,
        border: "1px solid",
        borderColor: alreadyMet ? "success.main" : `${accentColor}40`,
        position: "relative",
        overflow: "hidden",
        height: "100%",
      }}
    >
      {alreadyMet && (
        <Box
          sx={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: 3,
            bgcolor: "success.main",
            borderRadius: "12px 12px 0 0",
          }}
        />
      )}

      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5 }}>
        {icon}
        <Typography variant="subtitle2">{title}</Typography>
      </Box>

      {alreadyMet ? (
        <Typography variant="body1" color="success.main" fontWeight={600}>
          ✓ Meta ya alcanzada
        </Typography>
      ) : impossible ? (
        <Box>
          <Typography variant="h6" color="text.secondary">
            No calculable
          </Typography>
          <Typography variant="caption" color="text.secondary">
            El margen de este producto es insuficiente para alcanzar la meta
          </Typography>
        </Box>
      ) : (
        <>
          {/* Total units needed */}
          <Typography
            variant="h3"
            fontWeight={700}
            sx={{ color: accentColor, lineHeight: 1.1 }}
          >
            {additionalUnits?.toLocaleString("es-CL")}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            unidades adicionales
          </Typography>

          <Divider sx={{ my: 1.5 }} />

          {/* Rate info */}
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
            {currentRate && (
              <Typography variant="caption" color="text.secondary">
                Ritmo actual:{" "}
                <Box
                  component="span"
                  sx={{ color: "text.primary", fontWeight: 600 }}
                >
                  {currentRate} uds/día
                </Box>{" "}
                ({daysElapsed}d transcurridos)
              </Typography>
            )}
            {neededRate && daysRemaining > 0 && (
              <Typography
                variant="caption"
                sx={{ color: accentColor, fontWeight: 600 }}
              >
                Necesitas: {neededRate} uds/día en los próximos {daysRemaining}{" "}
                días
              </Typography>
            )}
            {daysRemaining === 0 && (
              <Typography variant="caption" color="error.main">
                Hoy es el último día del mes
              </Typography>
            )}
          </Box>
        </>
      )}
    </Paper>
  );
};

// ── ProjectionInput ───────────────────────────────────────────────────────────
const ProjectionInput = ({
  sim,
  ebt,
  ing,
  targetUnits,
  onTargetChange,
  daysRemaining,
}) => {
  const target = parseInt(targetUnits, 10);

  const projection = useMemo(() => {
    if (!sim || !ebt || !ing || isNaN(target) || target < 0) return null;
    const additional = target; // these are *additional* units on top of current
    const deltaMargen = additional * sim.avg_margen_sin_iva_per_unit;
    const deltaIngreso = additional * sim.avg_ingreso_sin_iva_per_unit;
    const projEbitda = ebt.ebitda + deltaMargen;
    const projIngreso = ing.total_ingreso_sin_iva + deltaIngreso;
    const projPct = projIngreso > 0 ? (projEbitda / projIngreso) * 100 : 0;
    const dailyRate =
      daysRemaining > 0 ? (target / daysRemaining).toFixed(1) : null;
    return {
      ebitda: projEbitda,
      ebitdaPct: Math.round(projPct * 10) / 10,
      ingreso: projIngreso,
      dailyRate,
    };
  }, [sim, ebt, ing, target, daysRemaining]);

  return (
    <Paper
      elevation={0}
      sx={{ p: 2.5, border: "1px solid #334155", height: "100%" }}
    >
      <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
        Simula tu propio escenario
      </Typography>
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ display: "block", mb: 2 }}
      >
        ¿Cuántas unidades adicionales planeas vender en los{" "}
        <Box component="span" sx={{ color: "primary.main", fontWeight: 600 }}>
          {daysRemaining} días restantes
        </Box>
        ?
      </Typography>

      <TextField
        type="number"
        label="Unidades adicionales"
        size="small"
        value={targetUnits}
        onChange={(e) => onTargetChange(e.target.value)}
        InputProps={{
          endAdornment: <InputAdornment position="end">uds.</InputAdornment>,
        }}
        inputProps={{ min: 0, step: 1 }}
        sx={{
          "& .MuiOutlinedInput-root": { bgcolor: "#0F172A" },
          mb: 2.5,
          maxWidth: 240,
          display: "block",
        }}
      />

      {projection && (
        <Box>
          <Box
            sx={{ display: "flex", alignItems: "baseline", gap: 1.5, mb: 0.5 }}
          >
            <Typography
              variant="h3"
              fontWeight={700}
              sx={{ color: ebitdaHex(projection.ebitdaPct), lineHeight: 1.1 }}
            >
              {projection.ebitdaPct > 0 ? "+" : ""}
              {projection.ebitdaPct}%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              EBITDA proyectado
            </Typography>
          </Box>

          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ display: "block", mb: 1.5 }}
          >
            {CLP(projection.ebitda)} · Ingreso proyectado:{" "}
            {CLP(projection.ingreso)}
          </Typography>

          {projection.dailyRate && (
            <Chip
              size="small"
              icon={<TimerIcon sx={{ fontSize: "14px !important" }} />}
              label={`${projection.dailyRate} uds/día durante ${daysRemaining} días`}
              color="primary"
              variant="outlined"
            />
          )}
        </Box>
      )}
    </Paper>
  );
};

// ── Main component ────────────────────────────────────────────────────────────
const ProjectionSimulator = ({
  salesLoaded,
  expensesLoaded,
  selectedMonth,
  isCurrentMonth,
  products,
}) => {
  const [product, setProduct] = useState(null);
  const [simData, setSimData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [targetUnits, setTargetUnits] = useState("");

  const { elapsed, remaining } = useMemo(getMonthDays, []);

  const fetchSim = useCallback(
    async (prod) => {
      setLoading(true);
      setError(null);
      try {
        const body = { producto: prod };
        if (selectedMonth && selectedMonth !== "all")
          body.month = selectedMonth;
        const res = await axios.post("/api/calculate/", body);
        setSimData(res.data);
        setTargetUnits("");
      } catch (err) {
        setError(err.response?.data?.error || "Error al calcular proyección");
      } finally {
        setLoading(false);
      }
    },
    [selectedMonth],
  );

  useEffect(() => {
    if (product) fetchSim(product);
    else {
      setSimData(null);
      setTargetUnits("");
    }
  }, [product, fetchSim]);

  useEffect(() => {
    if (product) fetchSim(product);
  }, [selectedMonth]); // eslint-disable-line

  // Only render for the current (open) month
  if (!isCurrentMonth || !salesLoaded || !expensesLoaded) return null;

  const sim = simData?.simulation;
  const ebt = simData?.ebitda;
  const ing = simData?.ingresos;

  return (
    <Paper elevation={0} sx={{ p: 3, border: "1px solid #1E293B", mt: 3 }}>
      {/* Header */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
        <CalculateIcon sx={{ color: "primary.main" }} />
        <Typography variant="subtitle2">
          ¿Cuánto Necesito Vender Este Mes?
        </Typography>
      </Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2.5 }}>
        <Typography variant="body2" color="text.secondary">
          Proyección para los días restantes del mes en curso. Llevas{" "}
          <Box component="span" sx={{ color: "text.primary", fontWeight: 600 }}>
            {elapsed} días
          </Box>{" "}
          transcurridos y quedan{" "}
          <Box component="span" sx={{ color: "primary.main", fontWeight: 600 }}>
            {remaining} días
          </Box>{" "}
          para cerrar el mes.
        </Typography>
      </Box>

      {/* Product selector */}
      <Autocomplete
        options={products}
        value={product}
        onChange={(_, val) => {
          setProduct(val);
          setTargetUnits("");
          setSimData(null);
        }}
        renderInput={(params) => (
          <TextField
            {...params}
            label="Selecciona un producto"
            size="small"
            sx={{ "& .MuiOutlinedInput-root": { bgcolor: "#0F172A" } }}
          />
        )}
        sx={{ maxWidth: 480, mb: sim && !loading ? 3 : 0 }}
      />

      {loading && (
        <Box sx={{ mt: 2 }}>
          <CircularProgress size={24} color="primary" />
        </Box>
      )}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {sim && !loading && (
        <>
          {/* Stats chips */}
          <Box sx={{ display: "flex", gap: 1.5, mb: 3, flexWrap: "wrap" }}>
            <Chip
              size="small"
              label={`Ya vendidas: ${sim.current_units.toLocaleString("es-CL")} uds. en ${elapsed}d`}
              variant="outlined"
            />
            <Chip
              size="small"
              label={`Ritmo actual: ${elapsed > 0 ? (sim.current_units / elapsed).toFixed(1) : "—"} uds/día`}
              variant="outlined"
            />
            <Chip
              size="small"
              label={`Margen por unidad: ${CLP(sim.avg_margen_sin_iva_per_unit)} (${sim.margen_pct}%)`}
              color={sim.margen_pct >= 25 ? "success" : "warning"}
              variant="outlined"
            />
          </Box>

          {/* Cards grid */}
          <Box sx={{ display: "flex", gap: 2, mb: 3, flexWrap: "wrap" }}>
            <Box sx={{ flex: "1 1 200px", minWidth: 0 }}>
              <TargetCard
                icon={<BalanceIcon sx={{ color: "#FBBF24", fontSize: 18 }} />}
                title="Punto de Equilibrio"
                alreadyMet={sim.already_breakeven}
                impossible={
                  sim.breakeven_units === null && !sim.already_breakeven
                }
                totalUnits={sim.total_for_breakeven}
                currentUnits={sim.current_units}
                additionalUnits={sim.breakeven_units}
                accentColor="#FBBF24"
                daysElapsed={elapsed}
                daysRemaining={remaining}
              />
            </Box>

            <Box sx={{ flex: "1 1 200px", minWidth: 0 }}>
              <TargetCard
                icon={
                  <TrendingUpIcon sx={{ color: "#22C55E", fontSize: 18 }} />
                }
                title="Meta EBITDA 25%"
                alreadyMet={sim.already_25pct}
                impossible={sim.target_25_units === null && !sim.already_25pct}
                totalUnits={sim.total_for_25pct}
                currentUnits={sim.current_units}
                additionalUnits={sim.target_25_units}
                accentColor="#22C55E"
                daysElapsed={elapsed}
                daysRemaining={remaining}
              />
            </Box>

            <Box sx={{ flex: "2 1 280px", minWidth: 0 }}>
              <ProjectionInput
                sim={sim}
                ebt={ebt}
                ing={ing}
                targetUnits={targetUnits}
                onTargetChange={setTargetUnits}
                daysRemaining={remaining}
              />
            </Box>
          </Box>

          {/* Disclaimer */}
          <Box
            sx={{
              bgcolor: "#0F172A",
              border: "1px solid #334155",
              borderRadius: 2,
              p: 2,
            }}
          >
            <Box sx={{ display: "flex", alignItems: "flex-start", gap: 1 }}>
              <InfoOutlinedIcon
                sx={{ fontSize: 15, color: "#475569", mt: 0.3, flexShrink: 0 }}
              />
              <Box>
                <Typography
                  variant="caption"
                  fontWeight={600}
                  sx={{ color: "#94A3B8", display: "block", mb: 0.5 }}
                >
                  Esta simulación es informativa y no constituye asesoría
                  profesional
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Los cálculos se basan en el promedio histórico del producto
                  seleccionado durante los {elapsed} días transcurridos, y
                  asumen que el precio, el costo de ingredientes y la demanda se
                  mantienen constantes en los {remaining} días restantes. En la
                  práctica los resultados varían por cambios en el mix de
                  ventas, costos de ingredientes, variaciones de demanda,
                  descuentos aplicados, nuevos gastos operacionales o
                  diferencias en el canal (local vs. Uber Eats). No constituye
                  asesoría financiera ni contable. Se recomienda complementar
                  con la revisión de un contador o asesor financiero antes de
                  tomar decisiones de negocio.
                </Typography>
              </Box>
            </Box>
          </Box>
        </>
      )}
    </Paper>
  );
};

export default ProjectionSimulator;
