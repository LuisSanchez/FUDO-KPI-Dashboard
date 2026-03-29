import React from "react";
import { Box, Typography, Tooltip } from "@mui/material";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

const KpiRow = ({ label, value, highlight, tooltip, dimmed }) => (
  <Box
    sx={{
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      py: 0.9,
      borderBottom: "1px solid",
      borderColor: "divider",
      opacity: dimmed ? 0.45 : 1,
    }}
  >
    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      {tooltip && (
        <Tooltip title={tooltip} arrow>
          <InfoOutlinedIcon
            sx={{ fontSize: 13, color: "#475569", cursor: "help" }}
          />
        </Tooltip>
      )}
    </Box>
    <Typography
      variant="body2"
      fontWeight={600}
      sx={{
        color:
          highlight === "pos"
            ? "success.main"
            : highlight === "neg"
              ? "error.main"
              : "text.primary",
      }}
    >
      {value}
    </Typography>
  </Box>
);

export default KpiRow;
