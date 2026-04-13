/**
 * Central Chart.js registration and shared theme defaults.
 * Import this file once before rendering any chart component.
 */
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  BarController,
  PointElement,
  LineElement,
  LineController,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { useContext, useMemo } from "react";
import { ColorModeContext } from "../ColorModeContext";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  BarController,
  PointElement,
  LineElement,
  LineController,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
);

// Static accent colors (same in both modes)
export const COLORS = {
  orange: "#F97316",
  orangeFade: "#F9731640",
  blue: "#3B82F6",
  blueFade: "#3B82F640",
  green: "#22C55E",
  greenFade: "#22C55E40",
  yellow: "#FBBF24",
  yellowFade: "#FBBF2440",
  red: "#EF4444",
  redFade: "#EF444440",
  slate: "#94A3B8",
  // dark-mode defaults kept for any non-chart code that still imports these
  grid: "#1E293B",
  gridLine: "#334155",
  text: "#94A3B8",
  textPrimary: "#F1F5F9",
};

// Palette for multi-series charts (pie, bar with many categories)
export const PALETTE = [
  "#F97316",
  "#3B82F6",
  "#22C55E",
  "#FBBF24",
  "#EF4444",
  "#A855F7",
  "#06B6D4",
  "#EC4899",
  "#84CC16",
  "#F59E0B",
  "#64748B",
];

// ── Adaptive color helpers ────────────────────────────────────────────────────

export const getChartColors = (isDark) => ({
  text: isDark ? "#94A3B8" : "#475569",
  textPrimary: isDark ? "#F1F5F9" : "#0F172A",
  gridLine: isDark ? "#334155" : "#E2E8F0",
  tooltipBg: isDark ? "#0F172A" : "#FFFFFF",
  tooltipBorder: isDark ? "#334155" : "#CBD5E1",
});

export const getBaseOptions = (isDark) => {
  const c = getChartColors(isDark);
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: c.text,
          font: { family: '"Inter", "Roboto", sans-serif', size: 12 },
          boxWidth: 12,
          padding: 16,
        },
      },
      tooltip: {
        backgroundColor: c.tooltipBg,
        borderColor: c.tooltipBorder,
        borderWidth: 1,
        titleColor: c.textPrimary,
        bodyColor: c.text,
        padding: 10,
        cornerRadius: 8,
      },
    },
    scales: {
      x: {
        ticks: { color: c.text, font: { size: 11 } },
        grid: { color: c.gridLine },
      },
      y: {
        ticks: { color: c.text, font: { size: 11 } },
        grid: { color: c.gridLine },
      },
    },
  };
};

export const getHorizontalBaseOptions = (isDark) => {
  const base = getBaseOptions(isDark);
  return {
    ...base,
    indexAxis: "y",
    scales: {
      x: { ...base.scales.x, grid: { color: base.scales.x.grid.color } },
      y: { ...base.scales.y, grid: { color: "transparent" } },
    },
  };
};

/** Hook for chart components — returns mode-aware colors and base options. */
export const useChartConfig = () => {
  const colorMode = useContext(ColorModeContext);
  const isDark = colorMode === "dark";
  const colors = useMemo(() => getChartColors(isDark), [isDark]);
  const baseOptions = useMemo(() => getBaseOptions(isDark), [isDark]);
  const horizontalBaseOptions = useMemo(
    () => getHorizontalBaseOptions(isDark),
    [isDark],
  );
  return { isDark, colors, baseOptions, horizontalBaseOptions };
};

// ── Backwards-compat static exports (dark-mode defaults) ─────────────────────
export const baseOptions = getBaseOptions(true);
export const horizontalBaseOptions = getHorizontalBaseOptions(true);

/** Format Chilean pesos */
export const CLP = (v) =>
  new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    minimumFractionDigits: 0,
  }).format(v);
