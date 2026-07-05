from app.services import indicators


def test_sma_basic():
    closes = [1, 2, 3, 4, 5]
    assert indicators.sma(closes, 3) == 4  # (3+4+5)/3
    assert indicators.sma(closes, 10) is None


def test_ema_converges_toward_recent_prices():
    closes = [10.0] * 30 + [20.0] * 30
    result = indicators.ema(closes, 12)
    assert result is not None
    # After 30 bars at 20, EMA(12) should be much closer to 20 than 10
    assert result > 17


def test_rsi_all_gains_is_100():
    closes = [float(i) for i in range(1, 20)]  # strictly increasing
    assert indicators.rsi(closes, 14) == 100.0


def test_rsi_all_losses_is_zero():
    closes = [float(i) for i in range(20, 1, -1)]  # strictly decreasing
    assert indicators.rsi(closes, 14) == 0.0


def test_rsi_insufficient_history_returns_none():
    assert indicators.rsi([1.0, 2.0, 3.0], 14) is None


def test_rsi_flat_prices_is_100_by_convention():
    # No losses at all -> avg_loss == 0 -> RSI defined as 100
    closes = [50.0] * 20
    assert indicators.rsi(closes, 14) == 100.0


def test_macd_returns_none_with_insufficient_history():
    closes = [float(i) for i in range(20)]
    assert indicators.macd(closes) is None


def test_macd_returns_three_values_with_sufficient_history():
    # slow(26) + signal(9) = 35 minimum bars
    closes = [100 + i * 0.5 for i in range(60)]
    result = indicators.macd(closes)
    assert result is not None
    macd_line, signal_line, histogram = result
    assert isinstance(macd_line, float)
    assert isinstance(signal_line, float)
    assert round(macd_line - signal_line, 4) == histogram


def test_pct_above_moving_average():
    assert indicators.pct_above_moving_average(110, 100) == 0.10
    assert indicators.pct_above_moving_average(90, 100) == -0.10
    assert indicators.pct_above_moving_average(100, None) is None
