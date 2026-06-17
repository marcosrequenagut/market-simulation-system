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
    order: tuple = (1, 1, 1),
    seasonal_order: tuple = (1, 1, 1, 5),
    test_size: float = 0.05,
    forecast_days: int = 30
):
    """
    Train a SARIMA model on closing prices and log results to MLflow.
    Uses d=1 differencing internally to handle non-stationarity.
    Reconstructs price from differenced predictions.

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
    series = df["close"]

    # Extracts just the closing prices as a pandas Series.
    # Stationarity check on original series and differenced series
    stationarity_original = check_stationarity(series)
    stationarity_differenced = check_stationarity(series.diff().dropna())  # Diff() calculates day-over-day changes
    
    print(f"Original series stationarity p-value: {stationarity_original['p_value']}")
    print(f"Differenced series stationarity p-value: {stationarity_differenced['p_value']}")
    print(f"Is stationary after diff: {stationarity_differenced['is_stationary']}")

    # Train/test split
    split_idx = int(len(series) * (1 - test_size))
    train = series[:split_idx]
    test = series[split_idx:]

    print(f"Train size: {len(train)} | Test size: {len(test)}")
    
    with mlflow.start_run(run_name=f"SARIMA_{ticker}"):
        
        # Log parameters
        mlflow.log_param("ticker", ticker)
        mlflow.log_param("model", "SARIMA")
        mlflow.log_param("order", str(order))
        mlflow.log_param("seasonal_order", str(seasonal_order))
        mlflow.log_param("train_size", len(train))
        mlflow.log_param("test_size", len(test))
        mlflow.log_param("forecast_days", forecast_days)
        mlflow.log_param("stationarity_p_value_original", stationarity_original["p_value"])
        mlflow.log_param("stationarity_p_value_diff", stationarity_differenced["p_value"])

        print("Training SARIMA model...")
        model = SARIMAX(
            train,
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
        # Generates predictions for all test period dates (1 year ahead from each point)
        forecast_test = fitted_model.forecast(steps=len(test))
        # Aligns predictions with actual dates for proper comparison
        forecast_test = pd.Series(forecast_test.values, index=test.index)

        # Metrics on price directly
        mae = mean_absolute_error(test, forecast_test)
        rmse = np.sqrt(mean_squared_error(test, forecast_test))
        mape = np.mean(np.abs((test.values - forecast_test.values) / test.values)) * 100
        
        print(f"Test MAE: {mae:.4f}")
        print(f"Test RMSE: {rmse:.4f}")
        print(f"Test MAPE: {mape:.4f}")
        
        mlflow.log_metric("test_mae", mae)
        mlflow.log_metric("test_rmse", rmse)
        mlflow.log_metric("test_mape", mape)
        mlflow.log_metric("aic", round(fitted_model.aic, 4))
        mlflow.log_metric("bic", round(fitted_model.bic, 4))

        # Future forecast
        # Predicts prices for next 365 business days (1 year ahead from last known date)
        future_forecast = fitted_model.forecast(steps=forecast_days)
        future_dates = pd.date_range(
            start=series.index[-1],  # Begins from last actual date
            periods=forecast_days + 1,  # Creates forecast_days+1 dates
            freq="B"  # business days only
        )[1:]  # Drops first date (which is the last known date)

        future_series = pd.Series(future_forecast.values, index=future_dates)

        # Confidence intervals
        forecast_result = fitted_model.get_forecast(steps=forecast_days)
        conf_int = forecast_result.conf_int()

        # Save backtest results
        backtest_df = pd.DataFrame({
            "date": test.index,
            "actual": test.values,
            "predicted": forecast_test.values
        })
        # Saves backtest results to CSV file
        backtest_path = f"ml/data/backtest_sarima_{ticker.replace('^', '')}.csv"
        backtest_df.to_csv(backtest_path, index=False)
        mlflow.log_artifact(backtest_path)

        # Save future forecast
        future_df = pd.DataFrame({
            "date": future_dates,
            "predicted": future_forecast.values,
            "lower_ci": conf_int.iloc[:, 0].values,
            "upper_ci": conf_int.iloc[:, 1].values
        })
        future_path = f"ml/data/future_sarima_{ticker.replace('^', '')}.csv"
        future_df.to_csv(future_path, index=False)
        mlflow.log_artifact(future_path)

        print(f"Future forecast saved {forecast_days} days ahead")
        print(f"Last known price: {series.iloc[-1]:.2f}")
        print(f"Forecast in {forecast_days} days: {future_series.iloc[-1]:.2f}")

        # Reemplaza esto:
        mlflow.statsmodels.log_model(fitted_model, "sarima_model")

        # Por esto:
        model_path = f"ml/data/model_sarima_{ticker.replace('^', '')}.pkl"
        fitted_model.save(model_path)
        mlflow.log_artifact(model_path)
        print("Run logged to MLflow")

    return fitted_model, future_df

if __name__ == "__main__":
    train_sarima(
        ticker="^GSPC",
        order=(1, 1, 1),
        seasonal_order=(1, 1, 1, 5),
        forecast_days=30
    )