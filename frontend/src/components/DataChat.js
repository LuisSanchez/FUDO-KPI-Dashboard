import { useEffect, useRef, useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Drawer,
  IconButton,
  TextField,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { askDataChat } from "../api/client";

const IDEAS = [
  "¿Cuál mes dejó peor EBITDA y qué lo explica?",
  "¿Cuánto entró de Uber en 2026 y cuánto se fue en anuncios?",
  "¿Qué proveedores pesan más en septiembre, sin préstamos?",
];

const DataChat = ({ open, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const bottom = useRef(null);

  useEffect(() => {
    const node = bottom.current;
    if (node && typeof node.scrollIntoView === "function") {
      node.scrollIntoView({ block: "end" });
    }
  }, [messages, sending, open]);

  const send = async (text) => {
    const question = text.trim();
    if (!question || sending) return;
    const history = [...messages, { role: "user", content: question }];
    setMessages(history);
    setDraft("");
    setError(null);
    setSending(true);
    try {
      const data = await askDataChat(history.map(({ role, content }) => ({ role, content })));
      setMessages([
        ...history,
        { role: "assistant", content: data.reply, consultas: data.consultas || [] },
      ]);
    } catch (err) {
      setError(err.response?.data?.error || "No se pudo consultar los números.");
    } finally {
      setSending(false);
    }
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: { xs: "100%", sm: 420 },
          maxWidth: "100%",
          display: "flex",
          flexDirection: "column",
        },
      }}
    >
      <Box
        sx={{
          px: 2,
          py: 1.5,
          display: "flex",
          alignItems: "center",
          gap: 1,
          borderBottom: "1px solid",
          borderColor: "divider",
        }}
      >
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="subtitle1" fontWeight={700}>
            Preguntar por los números
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Busca en las ventas, los gastos y las liquidaciones. No inventa montos.
          </Typography>
        </Box>
        <IconButton aria-label="Cerrar" onClick={onClose} size="small">
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>

      <Box sx={{ flex: 1, overflowY: "auto", px: 2, py: 2 }}>
        {messages.length === 0 && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            {IDEAS.map((idea) => (
              <Button
                key={idea}
                variant="outlined"
                size="small"
                onClick={() => send(idea)}
                disabled={sending}
                sx={{ justifyContent: "flex-start", textAlign: "left", textTransform: "none" }}
              >
                {idea}
              </Button>
            ))}
          </Box>
        )}
        {messages.map((message, index) => (
          <Box
            key={`${message.role}-${index}`}
            sx={{
              display: "flex",
              justifyContent: message.role === "user" ? "flex-end" : "flex-start",
              mb: 1.5,
            }}
          >
            <Box
              sx={{
                maxWidth: "90%",
                px: 1.5,
                py: 1,
                borderRadius: 2,
                bgcolor: message.role === "user" ? "primary.main" : "action.hover",
                color: message.role === "user" ? "primary.contrastText" : "text.primary",
              }}
            >
              <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
                {message.content}
              </Typography>
              {message.consultas?.length > 0 && (
                <Typography variant="caption" sx={{ display: "block", mt: 0.5, opacity: 0.8 }}>
                  Revisé la base · {message.consultas.length}{" "}
                  {message.consultas.length === 1 ? "consulta" : "consultas"}
                </Typography>
              )}
            </Box>
          </Box>
        ))}
        {sending && (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, color: "text.secondary" }}>
            <CircularProgress size={16} />
            <Typography variant="body2">Estoy mirando los números…</Typography>
          </Box>
        )}
        <div ref={bottom} />
      </Box>

      <Box sx={{ p: 2, borderTop: "1px solid", borderColor: "divider" }}>
        {error && (
          <Alert severity="error" sx={{ mb: 1.5 }}>
            {error}
          </Alert>
        )}
        <Box sx={{ display: "flex", gap: 1, alignItems: "flex-end" }}>
          <TextField
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                send(draft);
              }
            }}
            placeholder="Pregunta por un mes, un producto o un gasto"
            size="small"
            fullWidth
            multiline
            maxRows={4}
            disabled={sending}
            inputProps={{ "aria-label": "Pregunta sobre los números" }}
          />
          <Button variant="contained" onClick={() => send(draft)} disabled={sending || !draft.trim()}>
            Enviar
          </Button>
        </Box>
      </Box>
    </Drawer>
  );
};

export default DataChat;
