from fastapi import APIRouter, HTTPException, Query
from ml.predict import forecast_xgboost, forecast_sarima
import pandas as pd
import os

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/{ticker}")
def get_forecast(
    ticker: str,
    days: int = Query(default=30, ge=1, le=180, description="Business days to forecast"),
    model: str = Query(default="xgboost", description="Model to use: xgboost or sarima")
):
    try:
        if model == "sarima":
            df = forecast_sarima(ticker, days)
        else:
            df = forecast_xgboost(ticker, days)

        return {
            "ticker": ticker,
            "forecast_days": days,
            "last_known_price": round(float(df["previous_price"].iloc[0]), 2),
            "forecasted_price": round(float(df["predicted_price"].iloc[-1]), 2),
            "forecast": df.assign(
                date=df["date"].dt.strftime("%Y-%m-%d"),
                predicted_return=df["predicted_return"].round(6),
                previous_price=df["previous_price"].round(2),
                predicted_price=df["predicted_price"].round(2),
            ).to_dict(orient="records")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/backtest")
def get_backtest(ticker: str):
    clean_ticker = ticker.replace("^", "")
    path = f"ml/data/{clean_ticker}/backtest_xgb_{clean_ticker}.csv"

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Backtest data not found")
    
    try:
        df = pd.read_csv(path)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

        return {
            "ticker": ticker,
            "rows": len(df),
            "backtest": df.round(4).to_dict(orient="records")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))