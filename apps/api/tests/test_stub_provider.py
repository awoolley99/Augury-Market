from app.services.market_data.stub_provider import StubMarketDataProvider


def test_price_history_is_deterministic_per_ticker():
    provider = StubMarketDataProvider()
    first = provider.get_price_history("NVDA", days=100)
    second = provider.get_price_history("NVDA", days=100)
    assert [b.close for b in first] == [b.close for b in second]


def test_different_tickers_produce_different_series():
    provider = StubMarketDataProvider()
    nvda = provider.get_price_history("NVDA", days=100)
    tsla = provider.get_price_history("TSLA", days=100)
    assert [b.close for b in nvda] != [b.close for b in tsla]


def test_price_history_skips_weekends():
    provider = StubMarketDataProvider()
    bars = provider.get_price_history("AAPL", days=30)
    assert all(b.trade_date.weekday() < 5 for b in bars)


def test_price_history_ohlc_consistency():
    provider = StubMarketDataProvider()
    bars = provider.get_price_history("AAPL", days=50)
    for bar in bars:
        assert bar.high >= bar.open
        assert bar.high >= bar.close
        assert bar.low <= bar.open
        assert bar.low <= bar.close
        assert bar.volume > 0


def test_fundamentals_deterministic_and_bounded():
    provider = StubMarketDataProvider()
    f1 = provider.get_fundamentals("MSFT")
    f2 = provider.get_fundamentals("MSFT")
    assert f1 == f2
    assert 0 <= f1.institutional_ownership_pct <= 1
    assert f1.market_cap > 0


def test_news_is_sorted_most_recent_first():
    provider = StubMarketDataProvider()
    news = provider.get_recent_news("META", limit=5)
    dates = [n.published for n in news]
    assert dates == sorted(dates, reverse=True)
    assert all(-1.0 <= n.sentiment <= 1.0 for n in news)
