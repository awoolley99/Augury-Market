const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

const ACCESS_KEY = "augury.accessToken";
const REFRESH_KEY = "augury.refreshToken";

// Lets auth-context.tsx know whenever this module silently refreshes the
// access token in the background, so React state (and anything reading it)
// stays in sync instead of holding a stale token until the next full login.
let onTokenRefreshed: ((accessToken: string) => void) | null = null;
let onAuthExpired: (() => void) | null = null;

export function setTokenRefreshHandlers(handlers: {
  onTokenRefreshed?: (accessToken: string) => void;
  onAuthExpired?: () => void;
}) {
  onTokenRefreshed = handlers.onTokenRefreshed ?? null;
  onAuthExpired = handlers.onAuthExpired ?? null;
}

export function storeTokens(accessToken: string, refreshToken: string) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(ACCESS_KEY, accessToken);
  sessionStorage.setItem(REFRESH_KEY, refreshToken);
}

export function getStoredAccessToken(): string | null {
  return typeof window !== "undefined" ? sessionStorage.getItem(ACCESS_KEY) : null;
}

function getStoredRefreshToken(): string | null {
  return typeof window !== "undefined" ? sessionStorage.getItem(REFRESH_KEY) : null;
}

export function clearStoredTokens() {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(ACCESS_KEY);
  sessionStorage.removeItem(REFRESH_KEY);
}

// Bypasses the shared `request()` wrapper deliberately -- refreshing must
// never itself trigger another refresh-and-retry cycle.
async function rawRefresh(refreshToken: string): Promise<TokenPair> {
  const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) {
    throw new ApiError("Session expired", res.status);
  }
  return res.json();
}

const NO_RETRY_PATHS = ["/auth/login", "/auth/register", "/auth/refresh"];

async function request<T>(
  path: string,
  options: RequestInit & { token?: string; _isRetry?: boolean } = {}
): Promise<T> {
  const { token, headers, _isRetry, ...rest } = options;

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (!res.ok) {
    if (res.status === 401 && !_isRetry && !NO_RETRY_PATHS.includes(path)) {
      const refreshToken = getStoredRefreshToken();
      if (refreshToken) {
        try {
          const fresh = await rawRefresh(refreshToken);
          storeTokens(fresh.access_token, fresh.refresh_token);
          onTokenRefreshed?.(fresh.access_token);
          return request<T>(path, { ...options, token: fresh.access_token, _isRetry: true });
        } catch {
          clearStoredTokens();
          onAuthExpired?.();
        }
      } else {
        onAuthExpired?.();
      }
    }

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

export interface EvidencePacketRead {
  ticker: string;
  as_of_date: string;
  sector: string;
  close_price: number;
  sma_50: number | null;
  sma_200: number | null;
  rsi_14: number | null;
  macd_histogram: number | null;
  pct_above_sma_200: number | null;
  revenue_growth_yoy: number;
  pe_ratio: number | null;
  institutional_ownership_pct: number;
  market_cap: number;
  avg_news_sentiment: number;
  catalyst_count: number;
  news_headlines: string[];
  risk_score: number;
  risk_factors: string[];
  created_at: string;
}

export interface ScanRunResult {
  as_of_date: string;
  processed_count: number;
  failed_count: number;
  processed: string[];
  failed: string[];
}

export interface DimensionScoreRead {
  name: string;
  raw_value: number | null;
  score: number;
  weight: number;
  contribution: number;
}

export interface ConfidenceRead {
  ticker: string;
  total_score: number;
  recommendation: string;
  dimensions: DimensionScoreRead[];
  risk_adjustment_points: number;
  strengths: string[];
  risks: string[];
}

export interface AISummaryRead {
  ticker: string;
  as_of_date: string;
  provider: string;
  headline: string;
  why_it_ranked: string[];
  primary_risks: string[];
  suggested_hold_period: string;
  catalyst_strength: string;
  thesis_breakers: string[];
  confidence_score_at_generation: number;
  recommendation_at_generation: string;
  created_at: string;
}

export interface MarketOverviewRead {
  market_health_score: number;
  market_health_label: string;
  fear_greed_score: number;
  fear_greed_label: string;
  top_sector: string | null;
  top_sector_avg_score: number | null;
  tickers_scanned: number;
  catalyst_count_today: number;
}

export interface TopOpportunityRead {
  ticker: string;
  sector: string;
  confidence_score: number;
  recommendation: string;
  top_reason: string;
  personalized_rank_score: number;
}

export interface WatchlistSummaryItemRead {
  ticker: string;
  confidence_score: number | null;
  recommendation: string | null;
  score_change: number | null;
  top_reason: string | null;
}

export interface RecentReportRead {
  ticker: string;
  headline: string;
  recommendation: string;
  created_at: string;
}

export interface DashboardBriefingRead {
  market_overview: MarketOverviewRead;
  top_opportunities: TopOpportunityRead[];
  watchlist_summary: WatchlistSummaryItemRead[];
  recent_reports: RecentReportRead[];
}

export interface QuizOptionRead {
  letter: string;
  label: string;
}

export interface QuizQuestionRead {
  id: string;
  prompt: string;
  options: QuizOptionRead[];
}

export interface RiskProfileRead {
  risk_score: number;
  risk_level: string;
  answers: Record<string, string>;
  updated_at: string;
}

export interface BrokerageStatusRead {
  connected: boolean;
  provider: string | null;
  status: string | null;
  updated_at: string | null;
}

export interface BrokerageHoldingRead {
  symbol: string;
  quantity: number;
  market_value: number;
  account_name: string;
}

export interface BrokeragePortfolioRead {
  total_value: number;
  cash: number;
  holdings: BrokerageHoldingRead[];
  connected_accounts: string[];
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

  runScan: (token: string) =>
    request<ScanRunResult>("/scanner/run", { method: "POST", token }),

  listEvidence: (token: string, tickers?: string[]) =>
    request<EvidencePacketRead[]>(
      `/scanner/evidence${tickers && tickers.length ? `?tickers=${tickers.join(",")}` : ""}`,
      { token }
    ),

  listConfidence: (token: string, tickers?: string[]) =>
    request<ConfidenceRead[]>(
      `/confidence${tickers && tickers.length ? `?tickers=${tickers.join(",")}` : ""}`,
      { token }
    ),

  getSummary: (token: string, ticker: string, force?: boolean) =>
    request<AISummaryRead>(`/summary/${ticker}${force ? "?force=true" : ""}`, { token }),

  getBriefing: (token: string) =>
    request<DashboardBriefingRead>("/dashboard/briefing", { token }),

  getQuiz: (token: string) => request<QuizQuestionRead[]>("/quiz", { token }),

  getRiskProfile: (token: string) =>
    request<RiskProfileRead>("/quiz/profile", { token }),

  submitQuiz: (token: string, answers: Record<string, string>) =>
    request<RiskProfileRead>("/quiz/submit", {
      method: "POST",
      token,
      body: JSON.stringify({ answers }),
    }),

  getBrokerageStatus: (token: string) =>
    request<BrokerageStatusRead>("/brokerage/status", { token }),

  connectBrokerage: (token: string) =>
    request<{ connect_url: string }>("/brokerage/connect", { method: "POST", token }),

  getBrokeragePortfolio: (token: string) =>
    request<BrokeragePortfolioRead>("/brokerage/portfolio", { token }),

  disconnectBrokerage: (token: string) =>
    request<void>("/brokerage/connection", { method: "DELETE", token }),
};
