"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, WatchlistRead, ApiError } from "@/lib/api";

function firstName(fullName: string | null, email: string): string {
  if (fullName) return fullName.split(" ")[0];
  return email.split("@")[0];
}

export default function DashboardPage() {
  const { user, accessToken, loading, logout } = useAuth();
  const router = useRouter();
  const [watchlists, setWatchlists] = useState<WatchlistRead[]>([]);
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
        <p className="text-hush text-sm leading-relaxed">
          The scanner, confidence engine, and AI research reports aren&apos;t wired up yet —
          this milestone ships accounts and watchlists so the rest of the platform has
          somewhere real to attach to. Add tickers below to start tracking them.
        </p>
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
