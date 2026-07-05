# ADR 0005: Modular market-data provider interface

## Status
Accepted

## Context
Module 6 (Stock Scanner Engine) needs prices, volume, fundamentals, and news
for 1,000–2,000 tickers daily. No single provider is obviously correct at this
stage (Polygon, Alpaca, IEX, Finnhub all have different pricing/coverage
tradeoffs), and the choice may change as usage scales.

## Decision
Define a `MarketDataProvider` protocol (Milestone 2) with one implementation
per vendor, selected at runtime via `settings.MARKET_DATA_PROVIDER`. A `stub`
provider (fixture-based, no network calls) is the default in dev/test so the
scanner pipeline can be built and tested before a vendor contract is signed.

## Rationale
- Decouples the scanner pipeline's logic (indicator computation, evidence
  packet assembly) from any one vendor's API shape.
- Lets Milestone 2 development start immediately against the stub provider.
- Swapping or adding a provider later is a new adapter, not a rewrite.

## Consequences
- Each adapter must normalize its vendor's response into the same internal
  schema (OHLCV + fundamentals + news), which is extra upfront work per
  provider but pays for itself the first time a provider is swapped.
