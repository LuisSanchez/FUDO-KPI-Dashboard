import { useCallback, useEffect, useState } from "react";
import { getAuthConfig, getAuthMe } from "../api/client";

/** Optional auth state (no-op when backend OAuth disabled). */
export default function useAuth() {
  const [config, setConfig] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const cfg = await getAuthConfig();
      setConfig(cfg);
      if (cfg.oauth_enabled) {
        const me = await getAuthMe();
        setUser(me.authenticated ? me.user : null);
      } else {
        setUser(null);
      }
    } catch {
      setConfig({ oauth_enabled: false });
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const onAuthChange = useCallback((payload) => {
    setUser(payload?.authenticated ? payload.user : null);
  }, []);

  return {
    config,
    user,
    loading,
    refresh,
    onAuthChange,
    oauthEnabled: !!config?.oauth_enabled,
  };
}
