import { createTheme } from "@mui/material";

const createAppTheme = (mode) => {
  const isDark = mode === "dark";
  return createTheme({
    palette: {
      mode,
      primary: { main: "#F97316" },
      secondary: { main: "#94A3B8" },
      success: { main: "#22C55E" },
      error: { main: "#EF4444" },
      warning: { main: "#FBBF24" },
      background: isDark
        ? { default: "#0F172A", paper: "#1E293B" }
        : { default: "#F1F5F9", paper: "#FFFFFF" },
      text: isDark
        ? { primary: "#F1F5F9", secondary: "#94A3B8" }
        : { primary: "#0F172A", secondary: "#475569" },
      divider: isDark ? "#1E3A5F" : "#CBD5E1",
    },
    typography: {
      fontFamily: '"Inter", "Roboto", sans-serif',
      h4: { fontWeight: 700 },
      h6: { fontWeight: 600 },
      subtitle2: {
        fontWeight: 600,
        color: isDark ? "#94A3B8" : "#475569",
        textTransform: "uppercase",
        letterSpacing: "0.08em",
        fontSize: "0.7rem",
      },
    },
    shape: { borderRadius: 12 },
    components: {
      MuiPaper: { styleOverrides: { root: { backgroundImage: "none" } } },
      MuiDialog: {
        styleOverrides: { paper: { backgroundImage: "none" } },
      },
      MuiToggleButton: {
        styleOverrides: {
          root: {
            border: `1px solid ${isDark ? "#334155" : "#CBD5E1"}`,
            color: isDark ? "#94A3B8" : "#475569",
            textTransform: "none",
            "&.Mui-selected": {
              backgroundColor: "#F9731620",
              color: "#F97316",
              borderColor: "#F97316",
            },
          },
        },
      },
      MuiTableCell: {
        styleOverrides: {
          root: { borderColor: isDark ? "#334155" : "#E2E8F0" },
          head: {
            fontWeight: 600,
            color: isDark ? "#94A3B8" : "#475569",
            fontSize: "0.72rem",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            backgroundColor: isDark ? "#0F172A" : "#F8FAFC",
          },
        },
      },
    },
  });
};

export default createAppTheme;
