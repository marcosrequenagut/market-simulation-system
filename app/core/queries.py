from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from app.core.models import SP500Price


def get_prices(
    session: Session,
    start_date: date = None,
    end_date: date = None,
    limit: int = 100
) -> list[SP500Price]:
    """
    Get historical S&P 500 prices with optional date filters.

    Args:
        session: SQLAlchemy session
        start_date: Filter from this date (optional)
        end_date: Filter until this date (optional)
        limit: Maximum number of rows to return (default 100)

    Returns:
        List of SP500Price objects ordered by date ascending
    """
    query = session.query(SP500Price)

    if start_date:
        query = query.filter(SP500Price.date >= start_date)

    if end_date:
        query = query.filter(SP500Price.date <= end_date)

    return query.order_by(SP500Price.date.asc()).limit(limit).all()


def get_latest_price(session: Session) -> SP500Price:
    """
    Get the most recent S&P 500 price.

    Args:
        session: SQLAlchemy session

    Returns:
        Most recent SP500Price object
    """
    return session.query(SP500Price).order_by(SP500Price.date.desc()).first()


def get_daily_returns(
    session: Session,
    start_date: date = None,
    end_date: date = None,
) -> list[dict]:
    """
    Calculate daily returns from closing prices.

    Args:
        session: SQLAlchemy session
        start_date: Filter from this date (optional)
        end_date: Filter until this date (optional)

    Returns:
        List of dicts with date and daily return
    """
    prices = get_prices(session, start_date, end_date, limit=10000)

    returns = []
    for i in range(1, len(prices)):
        prev_close = prices[i - 1].close
        curr_close = prices[i].close
        daily_return = (curr_close - prev_close) / prev_close
        returns.append({
            "date": prices[i].date.isoformat(),
            "return": round(daily_return, 6),
            "cclose": curr_close
        })

    return returns


def get_price_since(
    session: Session,
    cutoff_date: date
) -> list[SP500Price]:
    """
    Get S&P 500 prices since a given cutoff date.

    Args:
        session: SQLAlchemy session
        cutoff_date: Start date to fetch prices from

    Returns:
        List of SP500Price objects ordered by date ascending
    """
    return (
        session.query(SP500Price)
        .filter(SP500Price.date >= cutoff_date)
        .order_by(SP500Price.date.asc())
        .all()
    )