import { useCallback, useEffect, useState } from "react";
import { fetchAuthConfig, fetchMe, loginWithGoogle, logout as apiLogout } from "../api/client";

export default function useAuth() {
  const [config, setConfig] = useState({ oauth_enabled: false, client_id: "", require_auth: false });
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [cfg, me] = await Promise.all([fetchAuthConfig(), fetchMe()]);
      setConfig(cfg);
      setUser(me.authenticated ? me : null);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const signInWithCredential = async (credential) => {
    const me = await loginWithGoogle(credential);
    setUser(me);
    return me;
  };

  const signOut = async () => {
    await apiLogout();
    setUser(null);
  };

  return { config, user, loading, refresh, signInWithCredential, signOut };
}
