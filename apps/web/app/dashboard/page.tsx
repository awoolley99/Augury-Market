"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, WatchlistRead, EvidencePacketRead, ApiError } from "@/lib/api";

function firstName(fullName: string | null, email: string): string {
  if (fullName) return fullName.split(" ")[0];
  return email.split("@")[0];
}

export default function DashboardPage() {
  const { user, accessToken, loading, logout } = useAuth();
  const router = useRouter();
  const [watchlists, setWatchlists] = useState<WatchlistRead[]>([]);
  const [evidence, setEvidence] = useState<EvidencePacketRead[]>([]);
  const [scanning, setScanning] = useState(false);
  const [scanMessage, setScanMessage] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [tickerDrafts, setTickerDrafts] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [dataLoading, setDataLoading] = useState(true);

  useEffect(() => {
    if (!loading && !accessToken) {
      router.push("/login");
    }
  }, [loading, accessToken, router]);

  useEffect(() => {
    if (!accessToken) return;
    api
      .listWatchlists(accessToken)
      .then(setWatchlists)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Couldn't load watchlists"))
      .finally(() => setDataLoading(false));
  }, [accessToken]);

  useEffect(() => {
    if (!accessToken) return;
    const allTickers = Array.from(new Set(watchlists.flatMap((w) => w.items.map((i) => i.ticker))));
    if (allTickers.length === 0) {
      setEvidence([]);
      return;
    }
    api
      .listEvidence(accessToken, allTickers)
      .then(setEvidence)
      .catch(() => setEvidence([]));
  }, [accessToken, watchlists]);

  async function handleRunScan() {
    if (!accessToken) return;
    setScanning(true);
    setScanMessage(null);
    try {
      const result = await api.runScan(accessToken);
      setScanMessage(
        `Scanned ${result.processed_count} tickers as of ${result.as_of_date}${
          result.failed_count > 0 ? ` (${result.failed_count} failed)` : ""
        }.`
      );
      const allTickers = Array.from(new Set(watchlists.flatMap((w) => w.items.map((i) => i.ticker))));
      if (allTickers.length > 0) {
        const fresh = await api.listEvidence(accessToken, allTickers);
        setEvidence(fresh);
      }
    } catch (err) {
      setScanMessage(err instanceof ApiError ? err.message : "Scan failed.");
    } finally {
      setScanning(false);
    }
  }

  async function handleCreateWatchlist(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken || !newName.trim()) return;
    try {
      const created = await api.createWatchlist(accessToken, newName.trim());
      setWatchlists((prev) => [...prev, created]);
      setNewName("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't create watchlist");
    }
  }

  async function handleDeleteWatchlist(id: string) {
    if (!accessToken) return;
    await api.deleteWatchlist(accessToken, id);
    setWatchlists((prev) => prev.filter((w) => w.id !== id));
  }

  async function handleAddTicker(watchlistId: string) {
    if (!accessToken) return;
    const ticker = tickerDrafts[watchlistId]?.trim();
    if (!ticker) return;
    try {
      const item = await api.addTicker(accessToken, watchlistId, ticker);
      setWatchlists((prev) =>
        prev.map((w) => (w.id === watchlistId ? { ...w, items: [...w.items, item] } : w))
      );
      setTickerDrafts((prev) => ({ ...prev, [watchlistId]: "" }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't add ticker");
    }
  }

  async function handleRemoveTicker(watchlistId: string, itemId: string) {
    if (!accessToken) return;
    await api.removeTicker(accessToken, watchlistId, itemId);
    setWatchlists((prev) =>
      prev.map((w) =>
        w.id === watchlistId ? { ...w, items: w.items.filter((i) => i.id !== itemId) } : w
      )
    );
  }

  if (loading || !user) {
    return (
      <main className="min-h-screen flex items-center justify-center text-hush">
        Reading the signs…
      </main>
    );
  }

  return (
    <main className="min-h-screen px-6 py-10 max-w-4xl mx-auto">
      <header className="flex items-start justify-between mb-10">
        <div>
          <p className="text-hush text-sm mb-1">Good morning, {firstName(user.full_name, user.email)}</p>
          <h1 className="font-display text-3xl text-parchment">Your briefing</h1>
        </div>
        <button
          onClick={logout}
          className="text-hush text-sm hover:text-parchment transition-colors"
        >
          Sign out
        </button>
      </header>

      <section className="rounded-lg border border-ink-700 bg-ink-900 p-5 mb-8">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-display text-xl text-parchment">Market snapshot</h2>
          <button
            onClick={handleRunScan}
            disabled={scanning}
            className="rounded-md bg-signal text-ink-950 text-sm font-medium px-3 py-1.5 hover:bg-signal-dim transition-colors disabled:opacity-50"
          >
            {scanning ? "Scanning…" : "Run scanner"}
          </button>
        </div>

        <p className="text-hush text-sm leading-relaxed mb-4">
          Raw scanner evidence (Module 6) for tickers on your watchlists — price, momentum,
          fundamentals, news sentiment, and a risk score. The Confidence Score Engine that
          turns this into a single Buy/Hold/Avoid rating isn&apos;t built yet (Milestone 3),
          so nothing below is a recommendation.
        </p>

        {scanMessage && <p className="text-signal text-sm mb-4">{scanMessage}</p>}

        {evidence.length === 0 ? (
          <p className="text-hush text-sm">
            No evidence yet. Add tickers to a watchlist below, then run the scanner.
          </p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {evidence.map((e) => (
              <div key={e.ticker} className="rounded-md border border-ink-700 bg-ink-800 p-4">
                <div className="flex items-baseline justify-between mb-2">
                  <span className="font-mono font-semibold text-parchment">{e.ticker}</span>
                  <span className="font-mono text-parchment">${e.close_price.toFixed(2)}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-hush mb-2">
                  <span>{e.sector}</span>
                  {e.pct_above_sma_200 !== null && (
                    <span className={e.pct_above_sma_200 >= 0 ? "text-rise" : "text-fall"}>
                      {e.pct_above_sma_200 >= 0 ? "+" : ""}
                      {(e.pct_above_sma_200 * 100).toFixed(1)}% vs 200-day
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <span className="text-hush">
                    RSI <span className="text-parchment font-mono">{e.rsi_14?.toFixed(0) ?? "—"}</span>
                  </span>
                  <span className="text-hush">
                    Sentiment{" "}
                    <span className={e.avg_news_sentiment >= 0 ? "text-rise font-mono" : "text-fall font-mono"}>
                      {e.avg_news_sentiment.toFixed(2)}
                    </span>
                  </span>
                  <span className="text-hush">
                    Risk <span className="text-signal font-mono">{e.risk_score}</span>
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="font-display text-xl text-parchment mb-4">Watchlists</h2>

        <form onSubmit={handleCreateWatchlist} className="flex gap-2 mb-6">
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="New watchlist name (e.g. AI Leaders)"
            className="flex-1 rounded-md bg-ink-800 border border-ink-700 px-3 py-2 text-parchment placeholder:text-hush/60 focus:outline-none focus:ring-2 focus:ring-signal/50"
          />
          <button
            type="submit"
            className="rounded-md bg-signal text-ink-950 font-medium px-4 py-2 hover:bg-signal-dim transition-colors"
          >
            Create
          </button>
        </form>

        {error && <p className="text-fall text-sm mb-4">{error}</p>}

        {dataLoading ? (
          <p className="text-hush text-sm">Loading watchlists…</p>
        ) : watchlists.length === 0 ? (
          <p className="text-hush text-sm">
            No watchlists yet. Create one above to start tracking tickers.
          </p>
        ) : (
          <div className="space-y-4">
            {watchlists.map((w) => (
              <div key={w.id} className="rounded-lg border border-ink-700 bg-ink-900 p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-display text-lg text-parchment">{w.name}</h3>
                  <button
                    onClick={() => handleDeleteWatchlist(w.id)}
                    className="text-hush text-xs hover:text-fall transition-colors"
                  >
                    Delete
                  </button>
                </div>

                {w.items.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-3">
                    {w.items.map((item) => (
                      <span
                        key={item.id}
                        className="inline-flex items-center gap-1.5 rounded-full bg-ink-800 border border-ink-700 px-3 py-1 text-sm font-mono text-parchment"
                      >
                        {item.ticker}
                        <button
                          onClick={() => handleRemoveTicker(w.id, item.id)}
                          aria-label={`Remove ${item.ticker}`}
                          className="text-hush hover:text-fall"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}

                <div className="flex gap-2">
                  <input
                    value={tickerDrafts[w.id] ?? ""}
                    onChange={(e) =>
                      setTickerDrafts((prev) => ({ ...prev, [w.id]: e.target.value }))
                    }
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleAddTicker(w.id);
                      }
                    }}
                    placeholder="Add ticker (e.g. NVDA)"
                    className="flex-1 rounded-md bg-ink-800 border border-ink-700 px-3 py-1.5 text-sm text-parchment placeholder:text-hush/60 focus:outline-none focus:ring-2 focus:ring-signal/50"
                  />
                  <button
                    onClick={() => handleAddTicker(w.id)}
                    className="rounded-md border border-ink-700 px-3 py-1.5 text-sm text-parchment hover:border-signal/50 transition-colors"
                  >
                    Add
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
