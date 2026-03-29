import React from "react";
import { Box, Typography } from "@mui/material";

/**
 * Horizontal progress bar showing EBITDA % relative to 0% (break-even)
 * and the 25% target. Range clamped to [-200%, +60%].
 */
const EbitdaGauge = ({ pct }) => {
  const clamp = Math.max(-200, Math.min(60, pct));
  const norm = ((clamp + 200) / 260) * 100;
  const zero = (200 / 260) * 100;
  const goal = ((200 + 25) / 260) * 100;

  return (
    <Box sx={{ mt: 2 }}>
      <Box
        sx={{
          position: "relative",
          height: 10,
          borderRadius: 5,
          bgcolor: "#0F172A",
          overflow: "hidden",
        }}
      >
        {pct >= 0 ? (
          <Box
            sx={{
              position: "absolute",
              left: `${zero}%`,
              top: 0,
              height: "100%",
              width: `${norm - zero}%`,
              bgcolor: pct >= 25 ? "#22C55E" : "#FBBF24",
              borderRadius: "0 5px 5px 0",
              transition: "width .6s ease",
            }}
          />
        ) : (
          <Box
            sx={{
              position: "absolute",
              left: `${norm}%`,
              top: 0,
              height: "100%",
              width: `${zero - norm}%`,
              bgcolor: "#EF4444",
              borderRadius: "5px 0 0 5px",
              transition: "width .6s ease",
            }}
          />
        )}
        {/* Zero marker */}
        <Box
          sx={{
            position: "absolute",
            left: `${zero}%`,
            top: 0,
            height: "100%",
            width: 2,
            bgcolor: "#475569",
          }}
        />
        {/* 25% goal marker */}
        <Box
          sx={{
            position: "absolute",
            left: `${goal}%`,
            top: 0,
            height: "100%",
            width: 2,
            bgcolor: "#F97316",
          }}
        />
      </Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", mt: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          Pérdida
        </Typography>
        <Typography variant="caption" color="text.secondary">
          0%
        </Typography>
        <Typography variant="caption" color="primary.main" fontWeight={600}>
          Meta 25%
        </Typography>
      </Box>
    </Box>
  );
};

export default EbitdaGauge;
