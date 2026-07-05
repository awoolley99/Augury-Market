"""
Technical indicators used by the scanner (Module 6). Pure functions over a
list of closing prices, oldest-first — no I/O, no DB, easy to unit test
against known values.
"""
from __future__ import annotations


def sma(closes: list[float], period: int) -> float | None:
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period


def ema_series(closes: list[float], period: int) -> list[float]:
    """Full EMA series (needed internally for MACD); same length as input
    once there are at least `period` values, empty before that."""
    if len(closes) < period:
        return []

    multiplier = 2 / (period + 1)
    ema_values = [sum(closes[:period]) / period]  # seed with SMA
    for price in closes[period:]:
        ema_values.append((price - ema_values[-1]) * multiplier + ema_values[-1])
    return ema_values


def ema(closes: list[float], period: int) -> float | None:
    series = ema_series(closes, period)
    return series[-1] if series else None


def rsi(closes: list[float], period: int = 14) -> float | None:
    """Wilder's RSI. Returns a 0-100 value, or None if there isn't enough
    history yet."""
    if len(closes) < period + 1:
        return None

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def macd(
    closes: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[float, float, float] | None:
    """Returns (macd_line, signal_line, histogram), or None if there isn't
    enough history for the slow EMA + signal smoothing yet."""
    if len(closes) < slow + signal:
        return None

    fast_series = ema_series(closes, fast)
    slow_series = ema_series(closes, slow)

    # Align: fast_series is longer (starts earlier) than slow_series since
    # `fast` < `slow`. Trim fast_series to the same tail length as slow_series.
    fast_series = fast_series[-len(slow_series):]

    macd_line_series = [f - s for f, s in zip(fast_series, slow_series)]
    signal_series = ema_series(macd_line_series, signal)

    if not signal_series:
        return None

    macd_line = macd_line_series[-1]
    signal_line = signal_series[-1]
    histogram = macd_line - signal_line

    return round(macd_line, 4), round(signal_line, 4), round(histogram, 4)


def pct_above_moving_average(current_price: float, moving_average: float | None) -> float | None:
    """How far `current_price` is above (positive) or below (negative) a
    moving average, as a fraction (0.05 == 5% above)."""
    if moving_average is None or moving_average == 0:
        return None
    return round((current_price - moving_average) / moving_average, 4)
