/**
 * Google Identity Services sign-in button (optional).
 * Only renders when backend reports oauth_enabled=true.
 * Set REACT_APP_GOOGLE_CLIENT_ID or rely on /api/auth/config/ response.
 */
import React, { useCallback, useEffect, useState } from "react";
import { Avatar, Box, Button, Chip, CircularProgress, Typography } from "@mui/material";
import LogoutIcon from "@mui/icons-material/Logout";
import axios from "axios";

function loadGisScript() {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) {
      resolve();
      return;
    }
    const existing = document.getElementById("google-gis");
    if (existing) {
      existing.addEventListener("load", () => resolve());
      return;
    }
    const s = document.createElement("script");
    s.id = "google-gis";
    s.src = "https://accounts.google.com/gsi/client";
    s.async = true;
    s.defer = true;
    s.onload = () => resolve();
    s.onerror = reject;
    document.head.appendChild(s);
  });
}

export default function GoogleSignIn({ onAuthChange }) {
  const [config, setConfig] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshMe = useCallback(async () => {
    try {
      const { data } = await axios.get("/api/auth/me/");
      setUser(data.authenticated ? data.user : null);
      onAuthChange?.(data);
    } catch {
      setUser(null);
    }
  }, [onAuthChange]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await axios.get("/api/auth/config/");
        if (cancelled) return;
        setConfig(data);
        if (data.oauth_enabled) {
          await refreshMe();
        }
      } catch {
        if (!cancelled) setConfig({ oauth_enabled: false });
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshMe]);

  const handleCredential = useCallback(
    async (response) => {
      try {
        const { data } = await axios.post("/api/auth/google/", {
          credential: response.credential,
        });
        setUser(data.user);
        onAuthChange?.({ authenticated: true, user: data.user });
      } catch (err) {
        console.error("Google login failed", err);
      }
    },
    [onAuthChange]
  );

  useEffect(() => {
    if (!config?.oauth_enabled || !config.google_client_id || user) return;
    let cancelled = false;
    (async () => {
      try {
        await loadGisScript();
        if (cancelled || !window.google?.accounts?.id) return;
        window.google.accounts.id.initialize({
          client_id: config.google_client_id,
          callback: handleCredential,
          auto_select: false,
        });
        const el = document.getElementById("google-signin-btn");
        if (el) {
          window.google.accounts.id.renderButton(el, {
            theme: "outline",
            size: "medium",
            text: "signin_with",
            shape: "rectangular",
          });
        }
      } catch (e) {
        console.warn("GIS load failed", e);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [config, user, handleCredential]);

  const handleLogout = async () => {
    await axios.post("/api/auth/logout/");
    setUser(null);
    onAuthChange?.({ authenticated: false, user: null });
  };

  if (loading) return <CircularProgress size={20} sx={{ color: "primary.main" }} />;
  if (!config?.oauth_enabled) return null;

  if (user) {
    return (
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        {user.avatar_url ? (
          <Avatar src={user.avatar_url} sx={{ width: 28, height: 28 }} />
        ) : null}
        <Typography variant="body2" sx={{ display: { xs: "none", sm: "block" } }}>
          {user.name || user.email}
        </Typography>
        <Chip size="small" label="Google" color="primary" variant="outlined" />
        <Button size="small" startIcon={<LogoutIcon />} onClick={handleLogout}>
          Salir
        </Button>
      </Box>
    );
  }

  return <Box id="google-signin-btn" sx={{ minHeight: 40 }} />;
}
