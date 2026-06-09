from unittest.mock import MagicMock
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.db import get_db
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


def get_mock_db(prices):
    """Return a mock db session with given prices."""
    def _mock_db():
        session = MagicMock()
        session.query.return_value.filter.return_value.order_by.return_value.first.return_value = prices[0] if prices else None
        session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = prices
        session.query.return_value.filter.return_value.order_by.return_value.all.return_value = prices
        session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = prices
        session.query.return_value.distinct.return_value.all.return_value = [("^GSPC",), ("^DJI",)]
        yield session
    return _mock_db


client = TestClient(app)


def test_get_latest_price():
    price = [make_price(date(2024, 1, 15), 4800.0)]
    app.dependency_overrides[get_db] = get_mock_db(price)
    response = client.get("/market/^GSPC/latest")
    assert response.status_code == 200
    assert response.json()["close"] == 4800.0
    app.dependency_overrides = {}


def test_get_latest_price_not_found():
    app.dependency_overrides[get_db] = get_mock_db([])
    response = client.get("/market/^GSPC/latest")
    assert response.status_code == 404
    app.dependency_overrides = {}


def test_get_available_tickers():
    app.dependency_overrides[get_db] = get_mock_db([])
    response = client.get("/market/tickers")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    app.dependency_overrides = {}


def test_get_prices():
    prices = [
        make_price(date(2024, 1, 1), 4700.0),
        make_price(date(2024, 1, 2), 4800.0),
    ]
    app.dependency_overrides[get_db] = get_mock_db(prices)
    response = client.get("/market/^GSPC/prices")
    assert response.status_code == 200
    assert len(response.json()) == 2
    app.dependency_overrides = {}


def test_get_prices_not_found():
    app.dependency_overrides[get_db] = get_mock_db([])
    response = client.get("/market/^GSPC/prices")
    assert response.status_code == 404
    app.dependency_overrides = {}


def test_get_price_history_default():
    prices = [make_price(date(2020, 1, i + 1), 3000.0 + i) for i in range(5)]
    app.dependency_overrides[get_db] = get_mock_db(prices)
    response = client.get("/market/^GSPC/history")
    assert response.status_code == 200
    assert len(response.json()) == 5
    app.dependency_overrides = {}


def test_get_price_history_with_years():
    prices = [make_price(date(2023, 1, i + 1), 4000.0 + i) for i in range(3)]
    app.dependency_overrides[get_db] = get_mock_db(prices)
    response = client.get("/market/^GSPC/history?years=5")
    assert response.status_code == 200
    app.dependency_overrides = {}


def test_get_price_history_with_days():
    prices = [make_price(date(2024, 1, i + 1), 4800.0 + i) for i in range(3)]
    app.dependency_overrides[get_db] = get_mock_db(prices)
    response = client.get("/market/^GSPC/history?days=30")
    assert response.status_code == 200
    app.dependency_overrides = {}


def test_get_price_history_not_found():
    app.dependency_overrides[get_db] = get_mock_db([])
    response = client.get("/market/^GSPC/history")
    assert response.status_code == 404
    app.dependency_overrides = {}


def test_get_ticker_stats():
    prices = [make_price(date(2020, 1, i + 1), 100.0 + i) for i in range(10)]
    app.dependency_overrides[get_db] = get_mock_db(prices)
    response = client.get("/market/^GSPC/stats")
    assert response.status_code == 200
    data = response.json()
    assert "annual_return" in data
    assert "annual_volatility" in data
    assert "cagr" in data
    app.dependency_overrides = {}


def test_get_daily_returns():
    prices = [
        make_price(date(2024, 1, 1), 100.0),
        make_price(date(2024, 1, 2), 110.0),
        make_price(date(2024, 1, 3), 105.0),
    ]
    app.dependency_overrides[get_db] = get_mock_db(prices)
    response = client.get("/market/^GSPC/returns")
    assert response.status_code == 200
    assert len(response.json()) == 2
    app.dependency_overrides = {}


def test_get_daily_returns_not_found():
    app.dependency_overrides[get_db] = get_mock_db([])
    response = client.get("/market/^GSPC/returns")
    assert response.status_code == 404
    app.dependency_overrides = {}
