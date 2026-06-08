from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.db import get_db
from app.core.queries  import get_prices, get_latest_price, get_daily_returns


router = APIRouter(prefix="/sp500", tags=["sp500"])


@router.get("/prices")
def prices(
    start_date: date = None,
    end_date: date = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get historical S&P 500 prices.
    Optional filters: start_date, end_date, limit.
    """
    data = get_prices(db, start_date, end_date, limit)
    if not data:
        raise HTTPException(status_code=404, detail="No data found")
    return [row.to_dict() for row in data]

@router.get("/latest")
def latest_price(db: Session = Depends(get_db)):
    """
    Get the latest S&P 500 price.
    """
    data = get_latest_price(db)
    if not data:
        raise HTTPException(status_code=404, detail="No data found")
    return data.to_dict()

@router.get("/returns")
def daily_returns(
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db)
):
    """
    Get daily returns for S&P 500.
    Optional filters: start_date, end_date.
    """
    data = get_daily_returns(db, start_date, end_date)
    if not data:
        raise HTTPException(status_code=404, detail="No data found")
    return [row.to_dict() for row in data]