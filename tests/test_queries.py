from datetime import date
from unittest.mock import MagicMock
from app.core.queries import (
    get_prices,
    get_available_tickers,
    get_last_date_for_ticker,
    get_latest_price,
    get_daily_returns,
    get_annualized_return
)
from app.core.models import MarketPrice

def make_price(d: date, close: float, ticker: str = "^GSPC") -> MarketPrice:
    """Helper to create a fake MarketPrice object."""
    p = MarketPrice()
    p.date = d
    p.ticker = ticker
    p.open = close
    p.high = close
    p.low = close
    p.close = close
    p.volume = 1000000
    return p


def mock_session(return_value):
    """Helper to create a mock SQLAlchemy session."""
    session = MagicMock()
    session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = return_value
    session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = return_value
    session.query.return_value.filter.return_value.order_by.return_value.first.return_value = return_value[0] if return_value else None
    session.query.return_value.filter.return_value.order_by.return_value.all.return_value = return_value
    session.query.return_value.distinct.return_value.all.return_value = [(t,) for t in set(p.ticker for p in return_value)]
    return session


def test_get_latest_price_returns_most_recent():
    price = make_price(date(2024, 1, 15), 4800.0)
    session = mock_session([price])
    result = get_latest_price(session, "^GSPC")
    assert result.close == 4800.0


def test_get_latest_price_no_data():
    session = MagicMock()
    session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    result = get_latest_price(session, "^GSPC")
    assert result is None


def test_get_available_tickers():
    prices = [
        make_price(date(2024, 1, 1), 100.0, "^GSPC"),
        make_price(date(2024, 1, 1), 200.0, "^DJI"),
    ]
    session = mock_session(prices)
    result = get_available_tickers(session)
    assert isinstance(result, list)


def test_get_annualized_return_basic():
    prices = [make_price(date(2020, 1, i + 1), 100.0 + i) for i in range(10)]
    session = MagicMock()
    session.query.return_value.filter.return_value.order_by.return_value.all.return_value = prices
    result = get_annualized_return(session, "^GSPC")
    assert "annual_return" in result
    assert "annual_volatility" in result
    assert "cagr" in result


def test_get_annualized_return_insufficient_data():
    prices = [make_price(date(2024, 1, 1), 100.0)]
    session = MagicMock()
    session.query.return_value.filter.return_value.order_by.return_value.all.return_value = prices
    result = get_annualized_return(session, "^GSPC")
    assert result["annual_return"] == 0.0
    assert result["annual_volatility"] == 0.0


def test_get_daily_returns_calculates_correctly():
    prices = [
        make_price(date(2024, 1, 1), 100.0),
        make_price(date(2024, 1, 2), 110.0),
        make_price(date(2024, 1, 3), 105.0),
    ]
    session = mock_session(prices)
    result = get_daily_returns(session, "^GSPC")
    assert len(result) == 2
    assert result[0]["return"] == round((110.0 - 100.0) / 100.0, 6)


def test_get_daily_returns_empty():
    session = mock_session([])
    result = get_daily_returns(session, "^GSPC")
    assert result == []
