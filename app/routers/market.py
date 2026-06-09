from datetime import date, timedelta
from pydantic import BaseModel
from typing import Annotated
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.db import get_db
from app.core.queries import (
    get_prices,
    get_latest_price,
    get_daily_returns,
    get_price_since,
    get_available_tickers,
    get_annualized_return,
    get_prices_since_multiple_tickers
)


router = APIRouter(prefix="/market", tags=["market"])
NO_DATA_FOUND = "No data found"


class CompareRequest(BaseModel):
    ticker: list[str]
    years: int = None
    days: int = None


@router.post("/compare", responses={400: {"description": "At least 2 tickers are required"}})
def compare_tickers(request: CompareRequest, db: Annotated[Session, Depends(get_db)]):
    """
    Get normalized price history (base 100) for multiple tickers.
    """
    if len(request.tickers) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 tickers are required"
        )

    if request.years is None and request.days is None:
        cutoff_date = date.today() - relativedelta(years=1)
    elif request.years is not None:
        cutoff_date = date.today() - relativedelta(years=request.years)
    elif request.days is not None:
        cutoff_date = date.today() - timedelta(days=request.days)

    data = get_prices_since_multiple_tickers(db, request.tickers, cutoff_date)

    result = {}
    for ticker, prices in data.items():
        if not prices:
            continue
        base = prices[0].close
        result[ticker] = [
            {
                "date": p.date.isoformat(),
                "value": round((p.close / base) * 100, 4)
            }
            for p in prices
        ]

    return result


@router.get("/tickers")
def available_tickers(db: Annotated[Session, Depends(get_db)]):
    """
    Get available tickers in the database.
    """
    return get_available_tickers(db)


@router.get("/{ticker}/prices", responses={404: {"description": "No data found"}})
def prices(
    db: Annotated[Session, Depends(get_db)],
    ticker: str,
    start_date: date = None,
    end_date: date = None,
    limit: int = 100
):
    """
    Get historical prices for a ticker.
    Optional filters: start_date, end_date, limit.
    """
    data = get_prices(db, ticker, start_date, end_date, limit)
    if not data:
        raise HTTPException(status_code=404, detail=NO_DATA_FOUND)
    return [row.to_dict() for row in data]


@router.get("/{ticker}/latest", responses={404: {"description": "No data found"}})
def latest_price(ticker: str, db: Annotated[Session, Depends(get_db)]):
    """
    Get the latest price for a ticker..
    """
    data = get_latest_price(db, ticker)
    if not data:
        raise HTTPException(status_code=404, detail=NO_DATA_FOUND)
    return data.to_dict()


@router.get("/{ticker}/returns", responses={404: {"description": "No data found"}})
def daily_returns(
    db: Annotated[Session, Depends(get_db)],
    ticker: str,
    start_date: date = None,
    end_date: date = None
):
    """
    Get daily returns for a ticker.
    Optional filters: start_date, end_date.
    """
    data = get_daily_returns(db, ticker, start_date, end_date)
    if not data:
        raise HTTPException(status_code=404, detail=NO_DATA_FOUND)
    return data


@router.get("/{ticker}/history", responses={404: {"description": "No data found"}})
def price_history(
    db: Annotated[Session, Depends(get_db)],
    ticker: str,
    years: int = None,
    days: int = None
):
    """
    Get price history for a ticker. Provide years or days as filter.
    Provide either years or days as filter.
    Default: 20 years.
    """
    if years is None and days is None:
        cutoff_date = date.today() - relativedelta(years=20)
    elif years is not None:
        cutoff_date = date.today() - relativedelta(years=years)
    else:
        cutoff_date = date.today() - timedelta(days=days)

    data = get_price_since(db, ticker, cutoff_date)
    if not data:
        raise HTTPException(status_code=404, detail=NO_DATA_FOUND)
    return [row.to_dict() for row in data]


@router.get("/{ticker}/stats", responses={404: {"description": "No data found"}})
def ticker_stats(ticker: str, db: Annotated[Session, Depends(get_db)]):
    """
    Get annualized return for a ticker.
    """
    data = get_annualized_return(db, ticker)
    if not data:
        raise HTTPException(status_code=404, detail=NO_DATA_FOUND)
    return data
