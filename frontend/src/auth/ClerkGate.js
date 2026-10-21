import React, { useEffect, useState } from "react";
import {
  ClerkLoading,
  ClerkProvider,
  HandleSSOCallback,
  Show,
  UserButton,
  useAuth,
  useSignIn,
} from "@clerk/react";
import {
  Alert,
  Box,
  Button,
  CssBaseline,
  LinearProgress,
  ThemeProvider,
  Typography,
} from "@mui/material";
import LocalPizzaIcon from "@mui/icons-material/LocalPizza";
import App from "../App";
import createAppTheme from "../theme";
import { setClerkTokenGetter } from "../api/client";

function colorMode() {
  const stored = localStorage.getItem("colorMode");
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function AuthedApp() {
  const { getToken, isLoaded } = useAuth();
  setClerkTokenGetter(getToken);
  useEffect(() => () => setClerkTokenGetter(null), []);
  if (!isLoaded) {
    return <LinearProgress color="primary" />;
  }
  return <App clerkEnabled userSlot={<UserButton />} />;
}

function SignedOutScreen() {
  const theme = createAppTheme(colorMode());
  const { signIn } = useSignIn();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  const enterWithGoogle = async () => {
    if (!signIn || pending) return;
    setError("");
    setPending(true);
    const result = await signIn.sso({
      strategy: "oauth_google",
      redirectUrl: "/",
      redirectCallbackUrl: "/sso-callback",
    });
    if (result?.error) {
      setPending(false);
      setError("No pude abrir Google. Activa Google como forma de entrada en Clerk.");
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          px: 2,
        }}
      >
        <Box sx={{ width: "100%", maxWidth: 420, textAlign: "center" }}>
          <LocalPizzaIcon sx={{ fontSize: 48, color: "primary.main", mb: 1 }} />
          <Typography variant="h4" sx={{ mb: 1 }}>
            Oh My Pizza
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>
            Entra con tu cuenta de Google para ver los números.
          </Typography>
          {error && (
            <Alert severity="error" sx={{ mb: 2, textAlign: "left" }}>
              {error}
            </Alert>
          )}
          <Button
            variant="contained"
            size="large"
            fullWidth
            onClick={enterWithGoogle}
            disabled={!signIn || pending}
          >
            {pending ? "Abriendo Google…" : "Entrar con Google"}
          </Button>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

function SSOCallback() {
  return (
    <HandleSSOCallback
      navigateToApp={({ decorateUrl }) => {
        window.location.assign(decorateUrl("/"));
      }}
      navigateToSignIn={() => {
        window.location.assign("/");
      }}
      navigateToSignUp={() => {
        window.location.assign("/");
      }}
    />
  );
}

export default function ClerkGate({ publishableKey }) {
  const returning = window.location.pathname === "/sso-callback";
  return (
    <ClerkProvider
      publishableKey={publishableKey}
      afterSignOutUrl="/"
      appearance={{ variables: { colorPrimary: "#F97316" } }}
    >
      {returning ? (
        <SSOCallback />
      ) : (
        <>
          <ClerkLoading>
            <LinearProgress color="primary" />
          </ClerkLoading>
          <Show when="signed-out">
            <SignedOutScreen />
          </Show>
          <Show when="signed-in">
            <AuthedApp />
          </Show>
        </>
      )}
    </ClerkProvider>
  );
}
