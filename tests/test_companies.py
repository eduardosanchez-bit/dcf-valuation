from dcf.companies import BY_TICKER, COMPANIES


def test_tickers_are_unique():
    tickers = [c.ticker for c in COMPANIES]
    assert len(tickers) == len(set(tickers))
    assert len(BY_TICKER) == len(COMPANIES)


def test_label_contains_name_and_ticker():
    c = BY_TICKER["AAPL"]
    assert "Apple" in c.label and "AAPL" in c.label
