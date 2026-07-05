"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, UserRead } from "./api";

interface AuthState {
  user: UserRead | null;
  accessToken: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

const STORAGE_KEY = "augury.accessToken";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserRead | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = typeof window !== "undefined" ? sessionStorage.getItem(STORAGE_KEY) : null;
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
      .catch(() => sessionStorage.removeItem(STORAGE_KEY))
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const tokens = await api.login(email, password);
    const profile = await api.me(tokens.access_token);
    sessionStorage.setItem(STORAGE_KEY, tokens.access_token);
    setAccessToken(tokens.access_token);
    setUser(profile);
  }

  async function register(email: string, password: string, fullName?: string) {
    await api.register(email, password, fullName);
    await login(email, password);
  }

  function logout() {
    sessionStorage.removeItem(STORAGE_KEY);
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
