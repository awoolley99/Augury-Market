const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, headers, ...rest } = options;

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(detail, res.status);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserRead {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
}

export interface WatchlistItemRead {
  id: string;
  ticker: string;
  added_at: string;
}

export interface WatchlistRead {
  id: string;
  name: string;
  created_at: string;
  items: WatchlistItemRead[];
}

export const api = {
  register: (email: string, password: string, fullName?: string) =>
    request<UserRead>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    }),

  login: (email: string, password: string) =>
    request<TokenPair>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: (token: string) => request<UserRead>("/auth/me", { token }),

  listWatchlists: (token: string) =>
    request<WatchlistRead[]>("/watchlists", { token }),

  createWatchlist: (token: string, name: string) =>
    request<WatchlistRead>("/watchlists", {
      method: "POST",
      token,
      body: JSON.stringify({ name }),
    }),

  deleteWatchlist: (token: string, watchlistId: string) =>
    request<void>(`/watchlists/${watchlistId}`, { method: "DELETE", token }),

  addTicker: (token: string, watchlistId: string, ticker: string) =>
    request<WatchlistItemRead>(`/watchlists/${watchlistId}/items`, {
      method: "POST",
      token,
      body: JSON.stringify({ ticker }),
    }),

  removeTicker: (token: string, watchlistId: string, itemId: string) =>
    request<void>(`/watchlists/${watchlistId}/items/${itemId}`, {
      method: "DELETE",
      token,
    }),
};
