import { createTheme } from "@mui/material";

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#F97316" },
    secondary: { main: "#94A3B8" },
    success: { main: "#22C55E" },
    error: { main: "#EF4444" },
    warning: { main: "#FBBF24" },
    background: { default: "#0F172A", paper: "#1E293B" },
    text: { primary: "#F1F5F9", secondary: "#94A3B8" },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", sans-serif',
    h4: { fontWeight: 700 },
    h6: { fontWeight: 600 },
    subtitle2: {
      fontWeight: 600,
      color: "#94A3B8",
      textTransform: "uppercase",
      letterSpacing: "0.08em",
      fontSize: "0.7rem",
    },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiPaper: { styleOverrides: { root: { backgroundImage: "none" } } },
    MuiDialog: {
      styleOverrides: {
        paper: { backgroundImage: "none", bgcolor: "#1E293B" },
      },
    },
    MuiToggleButton: {
      styleOverrides: {
        root: {
          border: "1px solid #334155",
          color: "#94A3B8",
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
        root: { borderColor: "#334155" },
        head: {
          fontWeight: 600,
          color: "#94A3B8",
          fontSize: "0.72rem",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          backgroundColor: "#0F172A",
        },
      },
    },
  },
});

export default theme;
