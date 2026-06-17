import warnings
import os
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
import mlflow.statsmodels
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
from sklearn.metrics import mean_squared_error, mean_absolute_error
from ml.features import load_prices

warnings.filterwarnings("ignore")

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/market_data")

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)


def check_stationarity(series: pd.Series) -> dict:
    """
    Run Augmented Dickey-Fuller test to check stationarity.

    Args:
        series: Time series to test

    Returns:
        Dictionary with test results
    """
    result = adfuller(series.dropna())
    return {
        'adf_statistic': round(result[0], 4),  # More negative = more stationary
        'p_value': round(result[1], 4),  # Probability series is non-stationary
        'is_stationary': result[1] < 0.05  # if p < 0.05 reject null hypotesis of non-stationarity
    }


def train_sarima(
    ticker: str = "^GSPC",
    order: tuple = (1, 0, 1),
    seasonal_order: tuple = (1, 0, 1, 5),
    test_size: float = 0.2,
    forecast_days: int = 30
):
    """
    Train a SARIMA model on daily returns (not absolute price) and log
    results to MLflow. Returns are stationary by nature, so no
    differencing (d=0) is typically needed, unlike with raw prices.
    Prices are reconstructed recursively from predicted returns,
    using the same approach as the XGBoost model for fair comparison.

    Args:
        ticker: Ticker symbol
        order: ARIMA order (p, d, q)
        seasonal_order: Seasonal order (P, D, Q, s)
        test_size: Fraction of data for testing
        forecast_days: Number of days to forecast into the future
    """
    print(f"Loading data for {ticker}...")
    df = load_prices(ticker)
    df = df.last("10Y")

    prices = df["close"]
    returns = prices.pct_change().dropna()

    # Extracts just the closing prices as a pandas returns.
    # Stationarity check on original returns and differenced returns
    stationarity_returns = check_stationarity(returns)
    
    print(f"Returns stationarity p-value: {stationarity_returns['p_value']}")
    print(f"Is stationary: {stationarity_returns['is_stationary']}")

    # Train/test split
    split_idx = int(len(returns) * (1 - test_size))
    train_returns = returns[:split_idx]
    test_returns = returns[split_idx:]

    print(f"Train size: {len(train_returns)} | Test size: {len(test_returns)}")
    
    with mlflow.start_run(run_name=f"SARIMA_{ticker}"):
        
        # Log parameters
        mlflow.log_param("ticker", ticker)
        mlflow.log_param("model", "SARIMA")
        mlflow.log_param("order", str(order))
        mlflow.log_param("seasonal_order", str(seasonal_order))
        mlflow.log_param("train_size", len(train_returns))
        mlflow.log_param("test_size", len(test_returns))
        mlflow.log_param("forecast_days", forecast_days)
        mlflow.log_param("stationarity_p_value", stationarity_returns["p_value"])
        mlflow.log_param("is_stationary", stationarity_returns["is_stationary"])

        print("Training SARIMA model...")
        model = SARIMAX(
            train_returns,
            order=order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        # Estimates optimal parameters using maximum likelihood
        # disp=False suppresses convergence messages
        # Returns fitted model object with learned coefficients
        fitted_model = model.fit(disp=False)

        # BACKTEST: predict on test set
        # Each predicted return is applied to the actual previous-day price,
        # so the model is only evaluated on a single-step-ahead basis
        # (errors do not accumulate)
        predicted_returns = fitted_model.forecast(steps=len(test_returns))
        predicted_returns.index = test_returns.index

        actual_prices = prices.loc[test_returns.index]
        previous_actual_prices = prices.shift(1).loc[test_returns.index]

        anchored_predicted_prices = previous_actual_prices * (1 + predicted_returns)

        # Metrics on price directly
        price_mae = mean_absolute_error(actual_prices, anchored_predicted_prices)
        price_rmse = np.sqrt(mean_squared_error(actual_prices, anchored_predicted_prices))
        price_mape = np.mean(np.abs((actual_prices.values - anchored_predicted_prices.values) / actual_prices.values)) * 100
        
        print(f"Test MAE: {price_mae:.4f}")
        print(f"Test RMSE: {price_rmse:.4f}")
        print(f"Test MAPE: {price_mape:.4f}")
        
        mlflow.log_metric("test_mae", price_mae)
        mlflow.log_metric("test_rmse", price_rmse)
        mlflow.log_metric("test_mape", price_mape)
        mlflow.log_metric("aic", round(fitted_model.aic, 4))
        mlflow.log_metric("bic", round(fitted_model.bic, 4))

        # Create a directory for each ticker
        ticker_dir = f"ml/data/{ticker.replace('^', '')}"
        os.makedirs(ticker_dir, exist_ok=True)

        # BACKTEST: cumulative version
        # Starts from the first real price in the test set and recursively
        # applies each predicted return to the previous PREDICTED price,
        # mirroring exactly how the future forecast behaves in production
        cumulative_prices = []
        current_price = float(prices.loc[train_returns.index[-1]])

        for predicted_return in predicted_returns.values:
            current_price = current_price * (1 + predicted_return)
            cumulative_prices.append(current_price)

        backtest_df = pd.DataFrame({
            "date": test_returns.index,
            "actual_return": test_returns.values,
            "predicted_return": predicted_returns.values,
            "actual_price": actual_prices.values,
            "predicted_price": anchored_predicted_prices.values,
            "predicted_price_cumulative": cumulative_prices
        })

        backtest_path = f"{ticker_dir}/backtest_sarima_{ticker.replace('^', '')}.csv"
        backtest_df.to_csv(backtest_path, index=False)
        mlflow.log_artifact(backtest_path)

        # Future forecast
        # Predicts prices for next 365 business days (1 year ahead from last known date)
        print(f"\nGenerating future forecast for {forecast_days} business days...")
        future_returns = fitted_model.forecast(steps=forecast_days)

        future_dates = pd.date_range(
            start=prices.index[-1],  # Begins from last actual date
            periods=forecast_days + 1,  # Creates forecast_days+1 dates
            freq="B"  # business days only
        )[1:]  # Drops first date (which is the last known date)

        last_known_price = float(prices.iloc[-1])
        current_price = last_known_price
        future_prices = []
        previous_prices = []

        for predicted_return in future_returns.values:
            previous_price = current_price
            current_price = current_price * (1 + predicted_return)
            previous_prices.append(previous_price)
            future_prices.append(current_price)

        future_df = pd.DataFrame({
            "date": future_dates,
            "predicted_return": future_returns.values,
            "previous_price": previous_prices,
            "predicted_price": future_prices
        })
        future_path = f"{ticker_dir}/future_sarima_{ticker.replace('^', '')}.csv"
        future_df.to_csv(future_path, index=False)
        mlflow.log_artifact(future_path)
        
        print(f"Last known price: {last_known_price:.2f}")
        print(f"Forecast in {forecast_days} business days: {future_prices[-1]:.2f}")

        # Register model in MLflow Model Registry
        model_name = f"sarima_model_{ticker.replace('^', '')}"
        mlflow.statsmodels.log_model(
            fitted_model,
            artifact_path="model",
            registered_model_name=model_name
        ) 

        print("Run logged to MLflow")

    return fitted_model, future_df

if __name__ == "__main__":
    train_sarima(
        ticker="^GSPC",
        order=(1, 0, 1),
        seasonal_order=(1, 0, 1, 5),
        forecast_days=30
    )