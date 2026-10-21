import React, { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  LinearProgress,
  MenuItem,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { fetchAiSettings, fetchOllamaModels, saveAiSettings } from "../api/client";

function errorText(err, fallback) {
  return err?.response?.data?.error || fallback;
}

export default function AiSettingsDialog({ open, onClose, clerkEnabled }) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down("sm"));
  const [form, setForm] = useState(null);
  const [models, setModels] = useState([]);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loadingModels, setLoadingModels] = useState(false);

  useEffect(() => {
    if (!open) return undefined;
    let cancelled = false;
    setError("");
    setSaved(false);
    setForm(null);
    fetchAiSettings()
      .then((data) => {
        if (!cancelled) setForm(data);
      })
      .catch((err) => {
        if (!cancelled) setError(errorText(err, "No pude cargar la configuración."));
      });
    return () => {
      cancelled = true;
    };
  }, [open]);

  const patch = (next) => {
    setSaved(false);
    setForm((current) => ({ ...current, ...next }));
  };

  const loadModels = async () => {
    setLoadingModels(true);
    setError("");
    try {
      const data = await fetchOllamaModels(form.ollama_base_url);
      const names = data.models || [];
      setModels(names);
      if (!names.length) {
        setError("Ollama no tiene modelos instalados.");
      } else if (!form.ollama_model) {
        patch({ ollama_model: names[0] });
      }
    } catch (err) {
      setError(errorText(err, "No pude llegar a Ollama."));
    } finally {
      setLoadingModels(false);
    }
  };

  const save = async () => {
    setSaving(true);
    setError("");
    setSaved(false);
    try {
      const data = await saveAiSettings({
        provider: form.provider,
        openrouter_model: form.openrouter_model,
        ollama_model: form.ollama_model,
        ollama_base_url: form.ollama_base_url,
      });
      setForm(data);
      setSaved(true);
    } catch (err) {
      setError(errorText(err, "No pude guardar la configuración."));
    } finally {
      setSaving(false);
    }
  };

  const modelOptions = [...new Set([form?.ollama_model, ...models].filter(Boolean))];
  const defaults = form?.defaults || {};

  return (
    <Dialog open={open} onClose={onClose} fullScreen={fullScreen} fullWidth maxWidth="sm">
      <DialogTitle>Configuración</DialogTitle>
      <DialogContent>
        <Box sx={{ color: "text.secondary", mb: 2 }}>
          Quién responde las preguntas sobre los números.
        </Box>
        {!clerkEnabled && (
          <Alert severity="info" sx={{ mb: 2 }}>
            El login está apagado hasta que agregues las claves de Clerk. Mientras tanto, esta
            pantalla queda abierta en este computador.
          </Alert>
        )}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        {saved && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Listo. El chat ya usa esta opción.
          </Alert>
        )}
        {!form ? (
          <LinearProgress />
        ) : (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <ToggleButtonGroup
              exclusive
              value={form.provider}
              onChange={(_event, value) => {
                if (value) patch({ provider: value });
              }}
              fullWidth
              size="small"
            >
              <ToggleButton value="openrouter">OpenRouter</ToggleButton>
              <ToggleButton value="ollama">Ollama en este computador</ToggleButton>
            </ToggleButtonGroup>
            {form.provider === "ollama" ? (
              <>
                <TextField
                  label="Dirección de Ollama"
                  value={form.ollama_base_url}
                  placeholder={defaults.ollama_base_url || "http://127.0.0.1:11434"}
                  onChange={(event) => patch({ ollama_base_url: event.target.value })}
                  helperText="Si el backend corre en Docker y Ollama en el Mac, usa http://host.docker.internal:11434."
                  fullWidth
                />
                <TextField
                  select
                  label="Modelo local"
                  value={form.ollama_model}
                  onChange={(event) => patch({ ollama_model: event.target.value })}
                  helperText="Pide la lista y elige cuál responde."
                  fullWidth
                >
                  {modelOptions.length === 0 && (
                    <MenuItem value="">Primero pulsa Ver modelos</MenuItem>
                  )}
                  {modelOptions.map((name) => (
                    <MenuItem key={name} value={name}>
                      {name}
                    </MenuItem>
                  ))}
                </TextField>
                <Button variant="outlined" onClick={loadModels} disabled={loadingModels}>
                  {loadingModels ? "Buscando…" : "Ver modelos"}
                </Button>
              </>
            ) : (
              <TextField
                label="Modelo de OpenRouter"
                value={form.openrouter_model}
                placeholder={defaults.openrouter_model || "x-ai/grok-4.7"}
                onChange={(event) => patch({ openrouter_model: event.target.value })}
                helperText="Si lo dejas vacío se usa el modelo del entorno."
                fullWidth
              />
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cerrar</Button>
        <Button variant="contained" onClick={save} disabled={!form || saving}>
          Guardar
        </Button>
      </DialogActions>
    </Dialog>
  );
}
