import { createContext, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as authApi from "../api/auth";
import { configureApiAuth, configureApiToken } from "../api/client";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [authStatus, setAuthStatus] = useState("bootstrapping");
  const accessTokenRef = useRef(null);
  const apiConfiguredRef = useRef(false);

  const applySession = useCallback((session) => {
    setUser(session.user);
    accessTokenRef.current = session.access_token || null;
  }, []);

  const clearAuth = useCallback(() => {
    setUser(null);
    accessTokenRef.current = null;
  }, []);

  const getAccessToken = useCallback(() => accessTokenRef.current, []);

  const restoreUser = useCallback(async () => {
    const profile = await authApi.getMe();
    setUser(profile);
    return profile;
  }, []);

  const refreshAccessToken = useCallback(async () => {
    const session = await authApi.refreshToken();
    accessTokenRef.current = session.access_token || null;
    return session.access_token;
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      clearAuth();
      setAuthStatus("unauthenticated");
      navigate("/login", { replace: true });
    }
  }, [clearAuth, navigate]);

  // Wire API clients synchronously on first render — guarantees token getter and
  // refresh handler are available before any child mounts or effects run.
  if (!apiConfiguredRef.current) {
    configureApiToken(getAccessToken);
    configureApiAuth(refreshAccessToken, logout);
    apiConfiguredRef.current = true;
  }

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      try {
        await refreshAccessToken();
        await restoreUser();
        if (active) setAuthStatus("authenticated");
      } catch {
        if (active) {
          clearAuth();
          setAuthStatus("unauthenticated");
        }
      }
    }

    bootstrap();
    return () => {
      active = false;
    };
  }, [clearAuth, refreshAccessToken, restoreUser]);

  const login = useCallback(
    async (email, password) => {
      const session = await authApi.login(email, password);
      applySession(session);
      await restoreUser();
      setAuthStatus("authenticated");
      return session.user;
    },
    [applySession, restoreUser],
  );

  const register = useCallback(
    async (email, password, name) => {
      const session = await authApi.register(email, password, name);
      applySession(session);
      await restoreUser();
      setAuthStatus("authenticated");
      return session.user;
    },
    [applySession, restoreUser],
  );

  const value = useMemo(
    () => ({
      user,
      authStatus,
      isLoading: authStatus === "bootstrapping",
      isAuthenticated: authStatus === "authenticated",
      getAccessToken,
      refreshAccessToken,
      login,
      register,
      logout,
      setUser,
    }),
    [user, authStatus, getAccessToken, refreshAccessToken, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
