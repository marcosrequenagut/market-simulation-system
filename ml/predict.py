import os
import pandas as pd
import xgboost as xgb
from ml.features import load_prices, build_features, FEATURE_COLUMNS
import mlflow
import mlflow.statsmodels

def load_xgb_model(ticker: str):
    """
    Load the latest registered XGBoost model for a given ticker from MLflow.

    Args:
        ticker: Ticker symbol

    Returns:
        Loaded XGBoost (xgboost) fitted model

    Raises:
        Exception: If no registered model exists for this ticker
    """
    model_name = f"xgboost_model_{ticker.replace('^', '')}"
    
    client = mlflow.tracking.MlflowClient()
    versions = client.search_model_versions(f"name='{model_name}'")
    
    if not versions:
        raise Exception(f"No registered model found for {model_name}")
    
    latest = sorted(versions, key=lambda v: int(v.version))[-1]
    
    model_uri = f"models:/{model_name}/{latest.version}"
    
    model = mlflow.xgboost.load_model(model_uri)
    return model

def load_sarima_model(ticker: str):
    """
    Load the latest registered SARIMA model for a given ticker from MLflow.

    Args:
        ticker: Ticker symbol

    Returns:
        Loaded SARIMA (statsmodels) fitted model

    Raises:
        Exception: If no registered model exists for this ticker
    """
    model_name = f"sarima_model_{ticker.replace('^', '')}"
    
    # Search the last registred version using the client HTTP
    client = mlflow.tracking.MlflowClient()
    versions = client.search_model_versions(f"name='{model_name}'")
    
    if not versions:
        raise Exception(f"No registered model found for {model_name}")
    
    # Take the version with the highest number
    latest = sorted(versions, key=lambda v: int(v.version))[-1]
    
    # Build URI with explicit version, not with 'latest'
    model_uri = f"models:/{model_name}/{latest.version}"
    
    model = mlflow.statsmodels.load_model(model_uri)
    return model


def forecast_xgboost(ticker: str, forecast_days: int = 30) -> pd.DataFrame:
    """
    Generate a recursive price forecast using a trained XGBoost model
    and the most recent real data from the database.

    Args:
        ticker: Ticker symbol
        forecast_days: Number of business days to forecast ahead

    Returns:
        DataFrame with date, predicted_return, previous_price, predicted_price
    """
    model = load_xgb_model(ticker)

    df = load_prices(ticker)
    df = df.last("10Y")  # enough history to compute rolling features
    df = build_features(df)

    X = df[FEATURE_COLUMNS]

    last_features = X.iloc[-1:].copy()
    last_known_price = float(df["close"].iloc[-1])
    current_price = last_known_price

    price_history = list(df["close"].iloc[-200:].values)

    future_prices = []
    future_returns = []
    previous_prices = []

    for _ in range(forecast_days):
        predicted_return = float(model.predict(last_features)[0])

        previous_price = current_price
        current_price = current_price * (1 + predicted_return)

        previous_prices.append(previous_price)
        future_returns.append(predicted_return)
        future_prices.append(current_price)

        price_history.append(current_price)
        prices_series = pd.Series(price_history)

        new_features = last_features.copy()
        new_features["return_1d"] = predicted_return
        new_features["return_5d"] = prices_series.pct_change(5).iloc[-1]
        new_features["return_20d"] = prices_series.pct_change(20).iloc[-1]

        ma_7 = prices_series.rolling(7).mean().iloc[-1]
        ma_21 = prices_series.rolling(21).mean().iloc[-1]
        ma_50 = prices_series.rolling(50).mean().iloc[-1]
        ma_200 = prices_series.rolling(200).mean().iloc[-1]

        new_features["ma_7_21_ratio"] = ma_7 / ma_21
        new_features["ma_21_50_ratio"] = ma_21 / ma_50
        new_features["price_ma200_ratio"] = current_price / ma_200

        vol_20 = prices_series.pct_change().rolling(20).std().iloc[-1] * (252 ** 0.5)
        vol_60 = prices_series.pct_change().rolling(60).std().iloc[-1] * (252 ** 0.5)
        new_features["volatility_20d"] = vol_20
        new_features["volatility_60d"] = vol_60

        delta = prices_series.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean().iloc[-1]
        rs = gain / loss if loss != 0 else 0
        new_features["rsi_14"] = 100 - (100 / (1 + rs)) if loss != 0 else 100

        bb_mid = prices_series.rolling(20).mean().iloc[-1]
        bb_std = prices_series.rolling(20).std().iloc[-1]
        bb_upper = bb_mid + 2 * bb_std
        bb_lower = bb_mid - 2 * bb_std
        new_features["bb_position"] = (current_price - bb_lower) / (bb_upper - bb_lower)

        last_features = new_features

    future_dates = pd.date_range(
        start=df.index[-1],
        periods=forecast_days + 1,
        freq="B"
    )[1:]

    result_df = pd.DataFrame({
        "date": future_dates,
        "predicted_return": future_returns,
        "previous_price": previous_prices,
        "predicted_price": future_prices
    })

    return result_df

def forecast_sarima(ticker: str, forecast_days: int = 30) -> pd.DataFrame:
    """
    Generate a price forecast using a trained SARIMA model
    and the most recent real data from the database.

    Args:
        ticker: Ticker symbol
        forecast_days: Number of business days to forecast ahead

    Returns:
        DataFrame with date, predicted_return, previous_price, predicted_price
    """
    model = load_sarima_model(ticker)

    df = load_prices(ticker)
    df = df.last("10Y")

    last_known_price = float(df["close"].iloc[-1])

    future_returns = model.forecast(steps=forecast_days)

    future_dates = pd.date_range(
        start=df.index[-1],
        periods=forecast_days + 1,
        freq="B"
    )[1:]

    current_price = last_known_price
    future_prices = []
    previous_prices = []

    for predicted_return in future_returns.values:
        previous_price = current_price
        current_price = current_price * (1 + predicted_return)
        previous_prices.append(previous_price)
        future_prices.append(current_price)

    result_df = pd.DataFrame({
        "date": future_dates,
        "predicted_return": future_returns.values,
        "previous_price": previous_prices,
        "predicted_price": future_prices
    })

    return result_df
