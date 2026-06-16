import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/market_data"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def load_prices(ticker: str) -> pd.DataFrame:
    """
    Load historical prices for a ticker from the database.

    Args:
        ticker: Ticker symbol

    Returns:
        DataFrame with date and close columns
    """
    query = f"""
        SELECT date, close
        FROM market_prices
        WHERE ticker = '{ticker}'
        ORDER BY date ASC
        """

    df = pd.read_sql(query, engine)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build features for ML models from price data.

    Args:
        df: DataFrame with close prices indexed by date

    Returns:
        DataFrame with engineered features
    """
    df = df.copy()

    # Returns
    df["return_1d"] = df["close"].pct_change(periods=1)
    df["return_5d"] = df["close"].pct_change(periods=5)
    df["return_20d"] = df["close"].pct_change(periods=20)
    
    # Moving averages
    df["ma_7"] = df["close"].rolling(window=5).mean()
    df["ma_21"] = df["close"].rolling(window=21).mean()
    df["ma_50"] = df["close"].rolling(window=50).mean()
    df["ma_200"] = df["close"].rolling(window=200).mean()
    
    # Moving average ratios
    df["ma_7_21_ratio"] = df["ma_7"] / df["ma_21"]
    df["ma_21_50_ratio"] = df["ma_21"] / df["ma_50"]
    df["price_ma200_ratio"] = df["close"] / df["ma_200"]
    
    # Volatility (rolling std of returns)
    df["volatility_20d"] = df["return_1d"].rolling(20).std() * (252 ** 0.5)
    df["volatility_60d"] = df["return_1d"].rolling(60).std() * (252 ** 0.5)

    # RSI: Relative Strenght Index (simplified)
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["rsi_14"] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    bb_mid = df["close"].rolling(20).mean()
    bb_std = df["close"].rolling(20).std()
    df["bb_upper"] = bb_mid + (2 * bb_std)
    df["bb_lower"] = bb_mid - (2 * bb_std)
    df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

    # Target: next day return (what we want to predict)
    df["target"] = df["close"].shift(-1)
    
    df = df.dropna()

    return df

FEATURE_COLUMNS = [
    "return_1d", "return_5d", "return_20d",
    "ma_7_21_ratio", "ma_21_50_ratio", "price_ma200_ratio",
    "volatility_20d", "volatility_60d",
    "rsi_14", "bb_position"
]