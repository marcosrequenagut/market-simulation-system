from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from app.core.models import MarketPrice
import math


def get_prices(
    session: Session,
    ticker: str,
    start_date: date = None,
    end_date: date = None,
    limit: int = 100
) -> list[MarketPrice]:
    """
    Get market prices for a given ticker with optional date filters.

    Args:
        session: SQLAlchemy session
        start_date: Filter from this date (optional)
        end_date: Filter until this date (optional)
        limit: Maximum number of rows to return (default 100)

    Returns:
        List of MarketPrice objects ordered by date ascending
    """
    query = session.query(MarketPrice).filter(MarketPrice.ticker == ticker)

    if start_date:
        query = query.filter(MarketPrice.date >= start_date)

    if end_date:
        query = query.filter(MarketPrice.date <= end_date)

    return query.order_by(MarketPrice.date.desc()).limit(limit).all()


def get_latest_price(session: Session, ticker: str) -> MarketPrice:
    """
    Get the most recent price for a given ticker.

    Args:
        session: SQLAlchemy session
        ticker: Ticker symbol

    Returns:
        Most recent MarketPrice object
    """
    return (
        session.query(MarketPrice)
        .filter(MarketPrice.ticker == ticker)
        .order_by(MarketPrice.date.desc())
        .first()
    )


def get_daily_returns(
    session: Session,
    ticker: str,
    start_date: date = None,
    end_date: date = None,
) -> list[dict]:
    """
    Calculate daily returns from closing prices for a given ticker.

    Args:
        session: SQLAlchemy session
        start_date: Filter from this date (optional)
        end_date: Filter until this date (optional)

    Returns:
        List of dicts with date and daily return
    """
    prices = get_prices(session, ticker, start_date, end_date, limit=10000)

    returns = []
    for i in range(1, len(prices)):
        prev_close = prices[i - 1].close
        curr_close = prices[i].close
        daily_return = (curr_close - prev_close) / prev_close
        returns.append({
            "date": prices[i].date.isoformat(),
            "ticker": ticker,
            "return": round(daily_return, 6),
            "cclose": curr_close
        })

    return returns


def get_price_since(
    session: Session,
    ticker: str,
    cutoff_date: date
) -> list[MarketPrice]:
    """
    Get market prices for a given ticker since a cutoff date.

    Args:
        session: SQLAlchemy session
        cutoff_date: Start date to fetch prices from

    Returns:
        List of MarketPrice objects ordered by date ascending
    """
    return (
        session.query(MarketPrice)
        .filter(MarketPrice.ticker == ticker)
        .filter(MarketPrice.date >= cutoff_date)
        .order_by(MarketPrice.date.asc())
        .all()
    )


def get_available_tickers(session: Session) -> list[str]:
    """
    Get all available tickers in the database.

    Args:
        session: SQLAlchemy session

    Returns:
        List of ticker strings
    """
    results = session.query(MarketPrice.ticker).distinct().all()
    return [r[0] for r in results]


def get_last_date_for_ticker(session: Session, ticker: str) -> Optional[date]:
    """
    Get the last date for a given ticker.

    Args:
        session: SQLAlchemy session
        ticker: Ticker symbol

    Returns:
        Last date for the ticker
    """
    result = (
        session.query(MarketPrice.date)
        .filter(MarketPrice.ticker == ticker)
        .order_by(MarketPrice.date.desc())
        .first()
    )
    return result[0] if result else None


def get_annualized_return(session: Session, ticker: str) -> dict:
    """
    Calculate annualized return and volatility for a given ticker.

    Args:
        session: SQLAlchemy session
        ticker: Ticker symbol

    Returns:
        Dictionary with annual_return and annual_volatility
    """
    prices = (
        session.query(MarketPrice)
        .filter(MarketPrice.ticker == ticker)
        .order_by(MarketPrice.date.asc())
        .all()
    )

    if len(prices) < 2:
        return {"annual_return": 0.0, "annual_volatility": 0.0}

    daily_returns = []
    for i in range(1, len(prices)):
        prev = prices[i - 1].close
        curr = prices[i].close
        daily_returns.append((curr - prev) / prev)

    avg_daily = sum(daily_returns) / len(daily_returns)
    annual_return = avg_daily * 252  # 252 is the numner of days where the market is open

    variance = sum((r - avg_daily) ** 2 for r in daily_returns) / len(daily_returns)
    annual_volatility = math.sqrt(variance) * math.sqrt(252)

    first_price = prices[0].close
    last_price = prices[-1].close
    years = len(prices) / 252

    cagr = (last_price / first_price) ** (1 / years) - 1

    return {
        "annual_return": round(annual_return, 4),
        "annual_volatility": round(annual_volatility, 4),
        "cagr": round(cagr, 4)
    }
