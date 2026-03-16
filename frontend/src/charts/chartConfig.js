/**
 * Central Chart.js registration and shared theme defaults.
 * Import this file once before rendering any chart component.
 */
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
);

// Shared palette aligned with the MUI dark theme
export const COLORS = {
  orange:      '#F97316',
  orangeFade:  '#F9731640',
  blue:        '#3B82F6',
  blueFade:    '#3B82F640',
  green:       '#22C55E',
  greenFade:   '#22C55E40',
  yellow:      '#FBBF24',
  yellowFade:  '#FBBF2440',
  red:         '#EF4444',
  redFade:     '#EF444440',
  slate:       '#94A3B8',
  grid:        '#1E293B',
  gridLine:    '#334155',
  text:        '#94A3B8',
  textPrimary: '#F1F5F9',
};

// Palette for multi-series charts (pie, bar with many categories)
export const PALETTE = [
  '#F97316', '#3B82F6', '#22C55E', '#FBBF24', '#EF4444',
  '#A855F7', '#06B6D4', '#EC4899', '#84CC16', '#F59E0B',
  '#64748B',
];

/** Base options shared by all chart types */
export const baseOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: COLORS.text,
        font: { family: '"Inter", "Roboto", sans-serif', size: 12 },
        boxWidth: 12,
        padding: 16,
      },
    },
    tooltip: {
      backgroundColor: '#0F172A',
      borderColor: '#334155',
      borderWidth: 1,
      titleColor: COLORS.textPrimary,
      bodyColor: COLORS.text,
      padding: 10,
      cornerRadius: 8,
    },
  },
  scales: {
    x: {
      ticks:  { color: COLORS.text, font: { size: 11 } },
      grid:   { color: COLORS.gridLine },
    },
    y: {
      ticks:  { color: COLORS.text, font: { size: 11 } },
      grid:   { color: COLORS.gridLine },
    },
  },
};

/** Horizontal bar variant (no y-grid, truncated labels) */
export const horizontalBaseOptions = {
  ...baseOptions,
  indexAxis: 'y',
  scales: {
    x: { ...baseOptions.scales.x, grid: { color: COLORS.gridLine } },
    y: { ...baseOptions.scales.y, grid: { color: 'transparent' } },
  },
};

/** Format Chilean pesos */
export const CLP = (v) =>
  new Intl.NumberFormat('es-CL', {
    style: 'currency', currency: 'CLP', minimumFractionDigits: 0,
  }).format(v);
