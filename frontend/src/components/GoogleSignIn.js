import React, { useEffect, useRef } from "react";
import { Box, Button, Avatar, Typography, Stack } from "@mui/material";

/**
 * Renders Google Identity Services button only when oauth is enabled.
 * Parent should pass clientId from /api/auth/config/ and handle credential.
 */
export default function GoogleSignIn({ clientId, enabled, user, onCredential, onSignOut }) {
  const btnRef = useRef(null);

  useEffect(() => {
    if (!enabled || !clientId || user) return undefined;

    const scriptId = "google-gsi";
    const init = () => {
      if (!window.google?.accounts?.id || !btnRef.current) return;
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => {
          if (response?.credential) onCredential(response.credential);
        },
      });
      btnRef.current.innerHTML = "";
      window.google.accounts.id.renderButton(btnRef.current, {
        theme: "outline",
        size: "medium",
        shape: "pill",
      });
    };

    if (!document.getElementById(scriptId)) {
      const s = document.createElement("script");
      s.src = "https://accounts.google.com/gsi/client";
      s.async = true;
      s.id = scriptId;
      s.onload = init;
      document.body.appendChild(s);
    } else {
      init();
    }
    return undefined;
  }, [enabled, clientId, user, onCredential]);

  if (!enabled) return null;

  if (user) {
    return (
      <Stack direction="row" spacing={1} alignItems="center">
        {user.avatar_url ? <Avatar src={user.avatar_url} sx={{ width: 28, height: 28 }} /> : null}
        <Typography variant="body2" noWrap sx={{ maxWidth: 140 }}>
          {user.display_name || user.email}
        </Typography>
        <Button size="small" color="inherit" onClick={onSignOut}>
          Salir
        </Button>
      </Stack>
    );
  }

  return <Box ref={btnRef} sx={{ minHeight: 40 }} />;
}
