import React from "react";
import { Paper, Box, Typography } from "@mui/material";
import { CLP } from "../utils/formatters";

const SimCard = ({
  icon,
  title,
  units,
  alreadyMet,
  impossible,
  product,
  extraRevenue,
}) => (
  <Paper
    elevation={0}
    sx={{
      p: 3,
      border: "1px solid",
      borderColor: alreadyMet
        ? "success.main"
        : impossible
          ? "#1E293B"
          : "divider",
      position: "relative",
      overflow: "hidden",
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
    <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
      {icon}
      <Typography variant="subtitle2">{title}</Typography>
    </Box>
    {alreadyMet ? (
      <Typography variant="h6" color="success.main">
        ✓ Ya alcanzado
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
      <Box>
        <Typography variant="h3" fontWeight={700} color="primary.main">
          {units?.toLocaleString("es-CL")}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          unidades adicionales de{" "}
          <strong style={{ color: "#F1F5F9" }}>{product}</strong>
        </Typography>
        {extraRevenue != null && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ display: "block", mt: 1 }}
          >
            ≈ {CLP(extraRevenue)} en ingresos adicionales (sin IVA)
          </Typography>
        )}
      </Box>
    )}
  </Paper>
);

export default SimCard;
