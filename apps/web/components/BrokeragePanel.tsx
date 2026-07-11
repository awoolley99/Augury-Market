"use client";

import { useEffect, useState } from "react";
import { api, BrokeragePortfolioRead, ApiError } from "@/lib/api";

export function BrokeragePanel({ accessToken }: { accessToken: string }) {
  const [connected, setConnected] = useState<boolean | null>(null);
  const [portfolio, setPortfolio] = useState<BrokeragePortfolioRead | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getBrokerageStatus(accessToken)
      .then((s) => setConnected(s.connected))
      .catch(() => setConnected(false));
  }, [accessToken]);

  useEffect(() => {
    if (!connected) return;
    api
      .getBrokeragePortfolio(accessToken)
      .then(setPortfolio)
      .catch(() => setPortfolio(null));
  }, [accessToken, connected]);

  async function handleConnect() {
    setConnecting(true);
    setError(null);
    try {
      const { connect_url } = await api.connectBrokerage(accessToken);
      // Real SnapTrade flow: this opens their hosted Connection Portal in a
      // new tab, where the user logs into Robinhood (or another brokerage)
      // directly -- never on this site. The stub provider just returns a
      // labeled placeholder URL instead.
      window.open(connect_url, "_blank", "noopener,noreferrer");
      // Give the (hypothetical) portal a moment, then check status. In the
      // stub case there's nothing to actually complete, so this is mostly
      // meaningful once a real provider is configured.
      setTimeout(async () => {
        const status = await api.getBrokerageStatus(accessToken);
        setConnected(status.connected);
      }, 1500);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't start the connection.");
    } finally {
      setConnecting(false);
    }
  }

  async function handleDisconnect() {
    await api.disconnectBrokerage(accessToken);
    setConnected(false);
    setPortfolio(null);
  }

  if (connected === null) return null; // still checking status

  return (
    <section className="rounded-lg border border-ink-700 bg-ink-900 p-5 mb-8">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-display text-xl text-parchment">Your portfolio</h2>
        {connected ? (
          <button
            onClick={handleDisconnect}
            className="text-hush text-xs hover:text-fall transition-colors"
          >
            Disconnect
          </button>
        ) : (
          <button
            onClick={handleConnect}
            disabled={connecting}
            className="rounded-md bg-signal text-ink-950 font-medium px-3 py-1.5 text-sm hover:bg-signal-dim transition-colors disabled:opacity-50"
          >
            {connecting ? "Connecting…" : "Connect brokerage account"}
          </button>
        )}
      </div>

      {error && <p className="text-fall text-sm mb-3">{error}</p>}

      {!connected ? (
        <p className="text-hush text-sm leading-relaxed">
          Link Robinhood (or another supported brokerage) to see your real holdings
          alongside Augury Market&apos;s research. Your login happens on the brokerage&apos;s
          own secure page — your credentials never touch this app.
        </p>
      ) : portfolio ? (
        <div>
          <div className="flex items-baseline gap-4 mb-4">
            <div>
              <p className="text-xs text-hush">Total value</p>
              <p className="font-mono text-2xl text-parchment">
                ${portfolio.total_value.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-hush">Cash</p>
              <p className="font-mono text-lg text-parchment">
                ${portfolio.cash.toLocaleString()}
              </p>
            </div>
          </div>
          <div className="space-y-1.5">
            {portfolio.holdings.map((h, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span className="font-mono text-parchment">{h.symbol}</span>
                <span className="text-hush text-xs">{h.quantity} shares</span>
                <span className="font-mono text-parchment">
                  ${h.market_value.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p className="text-hush text-sm">Loading your portfolio…</p>
      )}
    </section>
  );
}
