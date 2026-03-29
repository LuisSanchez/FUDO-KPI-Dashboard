// ── Currency & number formatters ──────────────────────────────────────────────

export const CLP = (v) =>
  new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    minimumFractionDigits: 0,
  }).format(v);

export const PCT = (v, decimals = 1) => `${Number(v).toFixed(decimals)}%`;

// ── Month helpers ─────────────────────────────────────────────────────────────

export const CURRENT_MONTH = new Date().toISOString().slice(0, 7); // "YYYY-MM"

export const MONTH_NAMES = {
  "01": "Enero",
  "02": "Febrero",
  "03": "Marzo",
  "04": "Abril",
  "05": "Mayo",
  "06": "Junio",
  "07": "Julio",
  "08": "Agosto",
  "09": "Sep",
  10: "Oct",
  11: "Nov",
  12: "Dic",
};

export const fmtMonth = (m) => {
  const [y, mo] = m.split("-");
  return `${MONTH_NAMES[mo]} ${y}`;
};

// ── Color helpers ─────────────────────────────────────────────────────────────

/** MUI color variant based on CMV percentage. */
export const cmvColor = (pct) =>
  pct <= 35 ? "success" : pct <= 42 ? "warning" : "error";

/** MUI color variant for expense type chips. */
export const TIPO_COLOR = {
  Operacional: "default",
  Préstamo: "warning",
  "Activo Fijo": "info",
};
