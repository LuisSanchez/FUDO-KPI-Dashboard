import React from "react";
import { useDropzone } from "react-dropzone";
import { Paper, Box, Typography } from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";

const DropzoneCard = ({ onDrop, title, subtitle, uploaded, fileName }) => {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
      "application/vnd.ms-excel": [".xls"],
    },
  });

  return (
    <Paper
      {...getRootProps()}
      elevation={0}
      sx={{
        p: 3,
        textAlign: "center",
        cursor: "pointer",
        transition: "all .2s",
        flex: 1,
        width: "100%",
        minHeight: 200,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        border: "2px dashed",
        borderColor: uploaded
          ? "success.main"
          : isDragActive
            ? "primary.main"
            : "#334155",
        bgcolor: uploaded
          ? "#22C55E10"
          : isDragActive
            ? "#F9731610"
            : "background.paper",
        "&:hover": {
          borderColor: uploaded ? "success.main" : "primary.main",
          transform: "translateY(-2px)",
          bgcolor: uploaded ? "#22C55E15" : "#F9731610",
        },
      }}
    >
      <input {...getInputProps()} />
      <Box sx={{ mb: 1.5 }}>
        {uploaded ? (
          <CheckCircleIcon sx={{ fontSize: 36, color: "success.main" }} />
        ) : (
          <UploadFileIcon
            sx={{
              fontSize: 36,
              color: isDragActive ? "primary.main" : "#475569",
            }}
          />
        )}
      </Box>
      <Typography variant="subtitle1" fontWeight={600} gutterBottom>
        {uploaded ? fileName : title}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {uploaded ? "Cargado · haz clic para reemplazar" : subtitle}
      </Typography>
    </Paper>
  );
};

export default DropzoneCard;
