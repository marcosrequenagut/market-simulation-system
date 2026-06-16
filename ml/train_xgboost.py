import os
import pandas as pd
import numpy as np
import mlflow
import mlflow.xgboost
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler
from ml.features import load_prices, build_features, FEATURE_COLUMNS

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)


def train_xgboost(
    ticker: str = "^GSPC",
    test_size: float = 0.2,
    forecast_days: int = 30,
    params: dict = None
):
    """
    Train an XGBoost model to forecast prices and log results to MLflow.

    Args:
        ticker: Ticker symbol
        test_size: Fraction of data for testing
        forecast_days: Number of days to forecast into the future
        params: XGBoost hyperparameters
    """
    if params is None:
        params = {
            "n_estimators": 500,
            "learning_rate": 0.05,
            "max_depth": 4,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42
        }

    print(f"Loading data for {ticker}...")
    df = load_prices(ticker)
    df = df.last("10Y")
    df = build_features(df)
    
    X = df[FEATURE_COLUMNS]
    y = df["target"]

    # Train/test split
    split_idx = int(len(df) * (1 - test_size))
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    print(f"Train size: {len(X_train)} | Test size: {len(X_test)}")

    with mlflow.start_run(run_name=f"xgboost_{ticker}"):
        mlflow.log_param("ticker", ticker)
        mlflow.log_param("model", "XGBoost")
        mlflow.log_param("train_size", len(X_train))
        mlflow.log_param("test_size", len(X_test))
        mlflow.log_param("forecast_days", forecast_days)
        mlflow.log_params(params)

        print("Training XGBoost model...")
        model = xgb.XGBRegressor(**params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )

        # Backtest
        y_pred = model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((y_test.values - y_pred) / y_test.values)) * 100

        print(f"MAE:  {mae:.2f}")
        print(f"RMSE: {rmse:.2f}")
        print(f"MAPE: {mape:.2f}%")

        mlflow.log_metric("mae", round(mae, 4))
        mlflow.log_metric("rmse", round(rmse, 4))
        mlflow.log_metric("mape", round(mape, 4))

        # Feature importance
        importance = pd.DataFrame({
            "feature": FEATURE_COLUMNS,
            "importance": model.feature_importances_
        }).sort_values("importance", ascending=False)

        print("\nTop 10 Feature Importances:")
        print(importance.to_string(index=False))

        importance_path = f"ml/data/feature_importance_xgb_{ticker.replace('^', '')}.csv"
        importance.to_csv(importance_path, index=False)
        mlflow.log_artifact(importance_path)

        # Backtest results
        backtest_df = pd.DataFrame({
            "date": X_test.index,
            "actual": y_test.values,
            "predicted": y_pred
        })
        backtest_path = f"ml/data/backtest_xgb_{ticker.replace('^', '')}.csv"
        backtest_df.to_csv(backtest_path, index=False)
        mlflow.log_artifact(backtest_path)

        # Future forecast
        print(f"\nGenerating {forecast_days}-day forecast...")
        last_features = X.iloc[-1:].copy()
        future_prices = []
        last_known_price = float(df["close"].iloc[-1])
        current_price = last_known_price

        for _ in range(forecast_days):
            pred_price = float(model.predict(last_features)[0])
            future_prices.append(pred_price)

            # Update features for next prediction (simplified)
            new_features = last_features.copy()
            new_features["return_1d"] = (pred_price - current_price) / current_price
            current_price = pred_price
            last_features = new_features

        future_dates = pd.date_range(
            start=X_test.index[-1],
            periods=forecast_days + 1,
            freq="B"
        )[1:]

        future_df = pd.DataFrame({
            "date": future_dates,
            "predicted": future_prices
        })
        future_path = f"ml/data/future_xgb_{ticker.replace('^', '')}.csv"
        future_df.to_csv(future_path, index=False)
        mlflow.log_artifact(future_path)

        model_path = f"ml/models/xgb_model_{ticker.replace('^', '')}.json"
        model.save_model(model_path)
        mlflow.log_artifact(model_path)

        print(f"Last known price: {last_known_price:.2f}")
        print(f"Forecast in {forecast_days} days: {future_prices[-1]:.2f}")
        print("Run logged to MLflow")

        return model, future_df


if __name__ == "__main__":
    train_xgboost(
        ticker="^GSPC",
        forecast_days=30
    )

        



