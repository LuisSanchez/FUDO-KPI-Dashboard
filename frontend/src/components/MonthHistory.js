import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { fetchMonthHistory, importMonthArchive, saveMonthSueldos } from "../api/client";
import { CLP, fmtMonth } from "../utils/formatters";

const MAX_SUELDOS = 100000000;

const optionalColor = (value, signed, strong) => {
  if (signed && value < 0) return "#EF4444";
  if (strong) return "primary.main";
  return "inherit";
};

const sticky = {
  position: "sticky",
  left: 0,
  bgcolor: "background.paper",
  zIndex: 1,
  whiteSpace: "nowrap",
};

const signedCLP = (value) => {
  if (value == null) return "—";
  const abs = CLP(Math.abs(value));
  if (value > 0) return `+${abs}`;
  if (value < 0) return `−${abs}`;
  return abs;
};

const signedPct = (value) => {
  if (value == null) return "—";
  const text = new Intl.NumberFormat("es-CL", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
    signDisplay: "exceptZero",
  }).format(value);
  return `${text}%`;
};

const tone = (value) => {
  if (value == null || value === 0) return "text.secondary";
  return value > 0 ? "#22C55E" : "#EF4444";
};

const MoneyCell = ({ value, strong }) => (
  <TableCell align="right" sx={{ whiteSpace: "nowrap", fontWeight: strong ? 700 : 400 }}>
    {CLP(value || 0)}
  </TableCell>
);

const ToneMoney = ({ value }) => (
  <TableCell
    align="right"
    sx={{ whiteSpace: "nowrap", fontWeight: 700, color: tone(value) }}
  >
    {value == null ? "—" : CLP(value)}
  </TableCell>
);

const DeltaCell = ({ value, money }) => (
  <TableCell align="right" sx={{ color: tone(value), whiteSpace: "nowrap", fontWeight: 600 }}>
    {money ? signedCLP(value) : signedPct(value)}
  </TableCell>
);

const OptionalMoney = ({ value, signed, strong }) => (
  <TableCell
    align="right"
    sx={{
      whiteSpace: "nowrap",
      fontWeight: strong ? 700 : 400,
      color: optionalColor(value, signed, strong),
    }}
  >
    {value == null ? "—" : signed ? signedCLP(value) : CLP(value)}
  </TableCell>
);

function DataTable({ columns, rows, highlight, onPick }) {
  return (
    <TableContainer sx={{ overflowX: "auto" }}>
      <Table size="small">
        <TableHead>
          <TableRow>
            {columns.map((column) => (
              <TableCell
                key={column.key}
                align={column.align || "right"}
                sx={column.key === "month" ? sticky : { whiteSpace: "nowrap" }}
              >
                {column.label}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row) => (
            <TableRow
              key={row.month}
              hover
              selected={row.month === highlight}
              onClick={onPick ? () => onPick(row.month) : undefined}
              sx={{
                cursor: onPick ? "pointer" : "default",
                bgcolor: row.month === highlight ? "action.hover" : undefined,
              }}
            >
              {columns.map((column) =>
                column.render ? (
                  <Fragment key={column.key}>{column.render(row)}</Fragment>
                ) : (
                  <TableCell
                    key={column.key}
                    align="left"
                    sx={{
                      ...sticky,
                      bgcolor: row.month === highlight ? "action.hover" : "background.paper",
                    }}
                  >
                    {fmtMonth(row.month)}
                  </TableCell>
                ),
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function Block({ title, subtitle, children }) {
  return (
    <Paper elevation={0} sx={{ p: { xs: 1.5, sm: 2.5 }, border: "1px solid", borderColor: "divider" }}>
      <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 0.5 }}>
        {title}
      </Typography>
      {subtitle && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {subtitle}
        </Typography>
      )}
      {children}
    </Paper>
  );
}

function Stat({ label, value, hint, colored }) {
  return (
    <Box>
      <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
        {label}
      </Typography>
      <Typography fontWeight={700} sx={{ color: colored ? tone(value) : "text.primary" }}>
        {value == null ? "—" : CLP(value)}
      </Typography>
      {hint && (
        <Typography variant="caption" color="text.secondary">
          {hint}
        </Typography>
      )}
    </Box>
  );
}

const MonthHistory = ({
  refreshKey = 0,
  selectedMonth = "all",
  onImported,
  onAvailability,
}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [pickedMonth, setPickedMonth] = useState(null);
  const [seenSelection, setSeenSelection] = useState(selectedMonth);
  const [draft, setDraft] = useState("");
  const onAvailabilityRef = useRef(onAvailability);
  onAvailabilityRef.current = onAvailability;

  const load = useCallback(async () => {
    setError(null);
    try {
      const next = await fetchMonthHistory();
      setData(next);
      onAvailabilityRef.current?.(Boolean(next.months?.length));
    } catch (err) {
      setError(err.response?.data?.error || "No se pudo cargar el historial");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  const months = data?.months;
  const rows = months || [];
  const defaultSueldos = data?.default_sueldos ?? 1300000;
  if (selectedMonth !== seenSelection) {
    setSeenSelection(selectedMonth);
    if (/^\d{4}-\d{2}$/.test(selectedMonth || "") && rows.some((row) => row.month === selectedMonth)) {
      setPickedMonth(selectedMonth);
    }
  }
  let evalMonth = null;
  if (pickedMonth && rows.some((row) => row.month === pickedMonth)) {
    evalMonth = pickedMonth;
  } else if (
    /^\d{4}-\d{2}$/.test(selectedMonth || "") &&
    rows.some((row) => row.month === selectedMonth)
  ) {
    evalMonth = selectedMonth;
  } else if (rows.length) {
    evalMonth = rows[rows.length - 1].month;
  }

  const evaluated = rows.find((row) => row.month === evalMonth) || null;
  const savedSueldos = evaluated ? (evaluated.sueldos_usados ?? defaultSueldos) : null;
  const fallbackSueldos = evaluated
    ? (evaluated.sueldos_sugerido ?? defaultSueldos)
    : defaultSueldos;

  useEffect(() => {
    if (savedSueldos == null) return;
    setDraft(String(savedSueldos));
  }, [evalMonth, savedSueldos]);

  const onImport = async () => {
    setImporting(true);
    setError(null);
    try {
      const imported = await importMonthArchive();
      onImported?.(imported);
      await load();
    } catch (err) {
      setError(err.response?.data?.error || "No se pudo cargar los archivos de 2026");
    } finally {
      setImporting(false);
    }
  };

  const draftNumber = /^\d+$/.test(draft) ? Number(draft) : null;
  const draftValid = draftNumber != null && draftNumber <= MAX_SUELDOS;
  const previewSueldos = draftValid ? draftNumber : savedSueldos;
  const gastosSin = evaluated?.gastos_sin_sueldos ?? 0;
  const previewEbitda =
    evaluated && previewSueldos != null
      ? evaluated.cobrado_sin_iva - gastosSin - previewSueldos
      : null;
  const previewResultado =
    previewEbitda == null ? null : previewEbitda - (evaluated?.comision_uber || 0);

  const persist = async (body) => {
    setSaving(true);
    setError(null);
    try {
      await saveMonthSueldos(body);
      await load();
    } catch (err) {
      setError(err.response?.data?.error || "No se pudo guardar el sueldo");
    } finally {
      setSaving(false);
    }
  };

  const onSave = () => {
    if (!evalMonth || !draftValid) {
      setError("El sueldo tiene que ser un entero entre 0 y 100.000.000.");
      return;
    }
    persist({ month: evalMonth, sueldos: draftNumber });
  };

  const onReset = () => {
    if (!evalMonth) return;
    setDraft(String(fallbackSueldos));
    if (savedSueldos === fallbackSueldos) return;
    persist({ month: evalMonth, reset: true });
  };

  const uberCollected = rows.reduce((sum, row) => sum + (row.uber?.cobrado || 0), 0);
  const uberEstimate = rows.reduce((sum, row) => sum + (row.uber?.neto_estimado || 0), 0);
  const pdfRows = rows.filter((row) => row.uber_pdf?.neto != null);
  const uberDeposit = pdfRows.reduce((sum, row) => sum + row.uber_pdf.neto, 0);

  const performanceColumns = [
    { key: "month", label: "Mes", align: "left" },
    {
      key: "tickets",
      label: "Tickets",
      render: (row) => (
        <TableCell align="right">{row.tickets.toLocaleString("es-CL")}</TableCell>
      ),
    },
    {
      key: "cobrado",
      label: "Cobrado s/IVA",
      render: (row) => <MoneyCell value={row.cobrado_sin_iva} />,
    },
    {
      key: "delta",
      label: "vs mes ant.",
      render: (row) => <DeltaCell value={row.delta_cobrado_pct} />,
    },
    {
      key: "gastos",
      label: "Gastos sin sueldos",
      render: (row) => <MoneyCell value={row.gastos_sin_sueldos} />,
    },
    {
      key: "sueldosArchivo",
      label: "Pago en archivo",
      render: (row) => <MoneyCell value={row.sueldos_fudo ?? row.sueldos} />,
    },
    {
      key: "previred",
      label: "Previred",
      render: (row) => <MoneyCell value={row.previred} />,
    },
    {
      key: "sueldos",
      label: "Sueldos usados",
      render: (row) => <MoneyCell value={row.sueldos_usados} strong />,
    },
    {
      key: "ebitda",
      label: "EBITDA",
      render: (row) => <ToneMoney value={row.ebitda} />,
    },
    {
      key: "resultado",
      label: "Después de Uber",
      render: (row) => <ToneMoney value={row.resultado} />,
    },
    {
      key: "deltaResultado",
      label: "vs mes ant.",
      render: (row) => <DeltaCell value={row.delta_resultado} money />,
    },
  ];

  const channelColumns = [
    { key: "month", label: "Mes", align: "left" },
    { key: "caja", label: "Caja", render: (row) => <MoneyCell value={row.channels?.caja} /> },
    { key: "walker", label: "Walker", render: (row) => <MoneyCell value={row.channels?.walker} /> },
    {
      key: "pya",
      label: "Pedidos Ya",
      render: (row) => <MoneyCell value={row.channels?.pedidos_ya} />,
    },
    {
      key: "uber",
      label: "Uber cobrado",
      render: (row) => <MoneyCell value={row.channels?.uber_eats} strong />,
    },
    { key: "otro", label: "Otro", render: (row) => <MoneyCell value={row.channels?.otro} /> },
    { key: "total", label: "Total", render: (row) => <MoneyCell value={row.cobrado} strong /> },
  ];

  const uberColumns = [
    { key: "month", label: "Mes", align: "left" },
    { key: "carta", label: "Carta", render: (row) => <MoneyCell value={row.uber?.carta} /> },
    {
      key: "descuentos",
      label: "Descuentos",
      render: (row) => <MoneyCell value={row.uber?.descuentos} />,
    },
    {
      key: "cobrado",
      label: "Pagó el cliente",
      render: (row) => <MoneyCell value={row.uber?.cobrado} />,
    },
    {
      key: "comision",
      label: "Comisión neta 26%",
      render: (row) => <MoneyCell value={row.uber?.comision_neta} />,
    },
    {
      key: "tasa",
      label: "Tasa estimada",
      render: (row) => <MoneyCell value={row.uber?.tasa_servicio} />,
    },
    {
      key: "neto",
      label: "Neto estimado",
      render: (row) => <MoneyCell value={row.uber?.neto_estimado} strong />,
    },
    {
      key: "deposito",
      label: "Depósito PDF",
      render: (row) => <OptionalMoney value={row.uber_pdf?.neto} strong />,
    },
    {
      key: "tasaPdf",
      label: "Tasa PDF",
      render: (row) => <OptionalMoney value={row.uber_pdf?.tasa} signed />,
    },
    {
      key: "anuncios",
      label: "Anuncios",
      render: (row) => <OptionalMoney value={row.uber_pdf?.anuncios} signed />,
    },
    {
      key: "ajustes",
      label: "Ajustes",
      render: (row) => <OptionalMoney value={row.uber_pdf?.ajustes} signed />,
    },
  ];

  const fuente =
    evaluated?.comision_fuente === "pdf" ? "Liquidación, sin IVA" : "Estimado 26%";

  return (
    <Box sx={{ mb: 3 }} data-testid="month-history">
      <Typography variant="h6" sx={{ mb: 0.5 }}>
        Meses anteriores
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Si el mes trae remuneraciones, parte de ese pago a la gente. Si no trae, o solo tiene pagos
        de prueba, parte en {CLP(defaultSueldos)}. Ese número reemplaza el pago a la gente, no se le
        suma, y no incluye Previred: el Previred se queda en los gastos cuando el archivo lo tiene.
        Subir un mes nuevo no borra los anteriores.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading && !data ? (
        <CircularProgress size={22} />
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {rows.length > 0 && (
            <Paper
              elevation={0}
              sx={{
                p: { xs: 2, sm: 2.5 },
                border: "1px solid",
                borderColor: "primary.main",
              }}
            >
              <Typography variant="caption" color="text.secondary" sx={{ letterSpacing: 0.4 }}>
                LO QUE ENTRA POR UBER EATS
              </Typography>
              <Typography variant="h5" fontWeight={700} color="primary.main">
                {CLP(pdfRows.length ? uberDeposit : uberEstimate)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {pdfRows.length
                  ? `Depósito de las liquidaciones en ${pdfRows.length} ${
                      pdfRows.length === 1 ? "mes" : "meses"
                    }. Ese número ya descontó tasa, cargo de la promo, anuncios, ajustes y reintegros. El estimado FUDO, antes de anuncios y financiamiento, suma ${CLP(
                      uberEstimate,
                    )} sobre ${CLP(uberCollected)} que pagó el cliente.`
                  : `No hay liquidaciones PDF para estos meses. El estimado, antes de anuncios y financiamiento, suma ${CLP(
                      uberEstimate,
                    )} sobre ${CLP(uberCollected)} que pagó el cliente.`}
              </Typography>
            </Paper>
          )}

          {evaluated && (
            <Paper
              elevation={0}
              data-testid="month-evaluator"
              sx={{ p: { xs: 2, sm: 2.5 }, border: "1px solid", borderColor: "divider" }}
            >
              <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 0.5 }}>
                Mes a evaluar: {fmtMonth(evaluated.month)}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                Se ven los dos resultados: el EBITDA, antes de la comisión de Uber, y el que queda
                después de esa comisión. El depósito del banco no se resta: es lo que llegó, y ya
                trae descontados anuncios y ajustes.{" "}
                {evaluated.tiene_remuneraciones
                  ? "El sueldo parte del pago a la gente que está en el archivo."
                  : `No hay remuneraciones en el archivo, así que el sueldo parte en ${CLP(
                      fallbackSueldos,
                    )}.`}
              </Typography>
              <ToggleButtonGroup
                value={evalMonth}
                exclusive
                size="small"
                onChange={(_, value) => value && setPickedMonth(value)}
                sx={{ display: "flex", flexWrap: "wrap", mb: 2 }}
              >
                {rows.map((row) => (
                  <ToggleButton key={row.month} value={row.month} disabled={saving}>
                    {fmtMonth(row.month)}
                  </ToggleButton>
                ))}
              </ToggleButtonGroup>
              <Box
                sx={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 1.5,
                  alignItems: "flex-start",
                  mb: 2,
                }}
              >
                <TextField
                  label="Sueldos del mes"
                  value={draft}
                  onChange={(event) => setDraft(event.target.value.replace(/\D/g, ""))}
                  size="small"
                  disabled={saving}
                  inputProps={{ inputMode: "numeric", "aria-label": "Sueldos del mes" }}
                  helperText={
                    draftValid
                      ? `Vas a usar ${CLP(draftNumber)}. En el archivo: ${CLP(
                          evaluated.sueldos_fudo || 0,
                        )}. Previred, aparte: ${CLP(evaluated.previred || 0)}.`
                      : "Escribe el sueldo, solo números. Puede ser 0."
                  }
                  sx={{ width: { xs: "100%", sm: 280 } }}
                />
                <Button
                  variant="contained"
                  onClick={onSave}
                  disabled={saving || !draftValid || draftNumber === savedSueldos}
                >
                  {saving ? "Guardando…" : "Usar este sueldo"}
                </Button>
                <Button
                  variant="text"
                  onClick={onReset}
                  disabled={
                    saving ||
                    (savedSueldos === fallbackSueldos && draftNumber === fallbackSueldos)
                  }
                >
                  Volver a {CLP(fallbackSueldos)}
                </Button>
              </Box>
              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: { xs: "1fr 1fr", md: "repeat(4, 1fr)" },
                  gap: 1.5,
                }}
              >
                <Stat label="Cobrado s/IVA" value={evaluated.cobrado_sin_iva} />
                <Stat label="Gastos sin sueldos" value={gastosSin} />
                <Stat label="Sueldos" value={previewSueldos} />
                <Stat label="Previred" value={evaluated.previred || 0} />
                <Stat label="EBITDA" value={previewEbitda} colored />
                <Stat label="Comisión Uber" value={evaluated.comision_uber} hint={fuente} />
                <Stat label="Después de Uber" value={previewResultado} colored />
                <Stat label="Depósito PDF" value={evaluated.uber_pdf?.neto ?? null} />
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 1.5 }}>
                El recuadro usa el sueldo escrito arriba. La tabla usa el último que guardaste.
              </Typography>
            </Paper>
          )}

          {rows.length > 0 && (
            <>
              <Block
                title="Performance"
                subtitle="EBITDA = cobrado sin IVA − gastos sin el pago a la gente − el sueldo de arriba. El Previred del archivo se queda en los gastos. Después de Uber resta la comisión neta: la del PDF sin IVA si hay liquidación, y si no el 26%. Préstamos y activo fijo quedan fuera. Pincha una fila para evaluarla."
              >
                <DataTable
                  columns={performanceColumns}
                  rows={rows}
                  highlight={evalMonth}
                  onPick={setPickedMonth}
                />
              </Block>
              <Block
                title="De dónde entra la plata"
                subtitle="Lo que pagó el cliente, con IVA, ya restados los descuentos. No es el precio de carta."
              >
                <DataTable
                  columns={channelColumns}
                  rows={rows}
                  highlight={evalMonth}
                  onPick={setPickedMonth}
                />
              </Block>
              <Block
                title="Uber Eats"
                subtitle="A la izquierda, el estimado de FUDO: 26% de lo que pagó el cliente, más el IVA de esa comisión. A la derecha, la liquidación. Si un mes no tiene PDF, esas celdas quedan en blanco."
              >
                <DataTable
                  columns={uberColumns}
                  rows={rows}
                  highlight={evalMonth}
                  onPick={setPickedMonth}
                />
              </Block>
            </>
          )}

          {data?.archive_available && (
            <Box>
              <Button variant={rows.length ? "text" : "contained"} onClick={onImport} disabled={importing}>
                {importing
                  ? "Cargando meses…"
                  : rows.length
                    ? "Actualizar con los archivos de 2026"
                    : "Cargar meses de 2026"}
              </Button>
              {!rows.length && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Lee las ventas y los gastos de docs/2026 y arma las tres tablas.
                </Typography>
              )}
            </Box>
          )}

          {!rows.length && !data?.archive_available && !loading && (
            <Typography variant="body2" color="text.secondary">
              Carga las ventas y los gastos de un mes. Al mes siguiente vuelve a cargarlos: este
              cuadro conserva los anteriores.
            </Typography>
          )}
        </Box>
      )}
    </Box>
  );
};

export default MonthHistory;
