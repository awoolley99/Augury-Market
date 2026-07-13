"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import {
  api,
  UserRead,
  storeTokens,
  getStoredAccessToken,
  clearStoredTokens,
  setTokenRefreshHandlers,
} from "./api";

interface AuthState {
  user: UserRead | null;
  accessToken: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserRead | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Whenever api.ts silently refreshes an expired access token in the
    // background (see request()'s 401-retry logic), keep React state in
    // sync so every component reading accessToken sees the fresh one --
    // otherwise components would keep sending the stale token until the
    // next full page load.
    setTokenRefreshHandlers({
      onTokenRefreshed: (fresh) => setAccessToken(fresh),
      onAuthExpired: () => {
        clearStoredTokens();
        setAccessToken(null);
        setUser(null);
      },
    });
    return () => setTokenRefreshHandlers({});
  }, []);

  useEffect(() => {
    const stored = getStoredAccessToken();
    if (!stored) {
      setLoading(false);
      return;
    }
    api
      .me(stored)
      .then((u) => {
        setUser(u);
        setAccessToken(stored);
      })
      .catch(() => clearStoredTokens())
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const tokens = await api.login(email, password);
    const profile = await api.me(tokens.access_token);
    storeTokens(tokens.access_token, tokens.refresh_token);
    setAccessToken(tokens.access_token);
    setUser(profile);
  }

  async function register(email: string, password: string, fullName?: string) {
    await api.register(email, password, fullName);
    await login(email, password);
  }

  function logout() {
    clearStoredTokens();
    setAccessToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, accessToken, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
