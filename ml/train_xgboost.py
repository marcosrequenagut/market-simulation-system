import os
import pandas as pd
import numpy as np
import mlflow
import mlflow.xgboost
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler
from ml.features import load_prices, build_features, FEATURE_COLUMNS
import os

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

        # Create a directory for each ticker
        ticker_dir = f"ml/data/{ticker.replace('^', '')}"
        os.makedirs(ticker_dir, exist_ok=True)

        # Feature importance
        importance = pd.DataFrame({
            "feature": FEATURE_COLUMNS,
            "importance": model.feature_importances_
        }).sort_values("importance", ascending=False)

        print("\nTop 10 Feature Importances:")
        print(importance.to_string(index=False))

        importance_path = f"{ticker_dir}/feature_importance_xgb_{ticker.replace('^', '')}.csv"
        importance.to_csv(importance_path, index=False)
        mlflow.log_artifact(importance_path)

        # Backtest results
        # Reconstruct prices from predicted returns to visually compare against actual prices
        actual_prices = df["close"].iloc[split_idx:split_idx + len(y_test)].values

        # Predicted price = previous actual price * (1 + predicted return)
        predicted_prices_backtest = actual_prices[:-1] * (1 + y_pred[:-1])
        
        # Align: first predicted price has no "previuous actual" before test set, so we use the last known train price for the first prediction
        last_train_price = float(df["close"].iloc[split_idx -1])
        predicted_prices_backtest = np.insert(predicted_prices_backtest, 0, last_train_price * (1 + y_pred[0]))

        # Normal backtest and cumulative return backtest
        predicted_prices_cumulative = [last_train_price]
        for ret in y_pred:
            predicted_prices_cumulative.append(predicted_prices_cumulative[-1] * (1 + ret))
        predicted_prices_cumulative = np.array(predicted_prices_cumulative[1:])
        
        backtest_df = pd.DataFrame({
            "date": X_test.index,
            "actual_return": y_test.values,
            "predicted_return": y_pred,
            "actual_price": actual_prices,
            "predicted_price": predicted_prices_backtest,
            "predicted_price_cumulative": predicted_prices_cumulative
        })

        backtest_path = f"{ticker_dir}/backtest_xgb_{ticker.replace('^', '')}.csv"
        backtest_df.to_csv(backtest_path, index=False)
        mlflow.log_artifact(backtest_path)

        # Price based metrics 
        price_mae = mean_absolute_error(actual_prices, predicted_prices_backtest)
        price_mape = np.mean(np.abs((actual_prices - predicted_prices_backtest) / actual_prices)) * 100

        mlflow.log_metric("price_mae", round(price_mae, 4))
        mlflow.log_metric("price_mape", round(price_mape, 4))

        print(f"\nPrice MAE: {price_mae:.4f}")
        print(f"Price MAPE: {price_mape:.2f}%")

        # Future forecast
        print(f"\nGenerating {forecast_days}-day forecast...")
        future_prices = []
        future_returns = []
        previous_prices = []

        last_known_price = float(df["close"].iloc[-1])
        current_price = last_known_price

        # Keep a rolling window of recent prices (real + simulated) to recompute features
        price_history = list(df["close"].iloc[-200:].values)

        last_features = X.iloc[-1:].copy()

        for _ in range(forecast_days):
            predicted_return = float(model.predict(last_features)[0])

            previous_price = current_price
            current_price = current_price * (1 + predicted_return)

            previous_prices.append(previous_price)
            future_returns.append(predicted_return)
            future_prices.append(current_price)

            price_history.append(current_price)

            # Recompute features based on updated rolling price history
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
            start=X_test.index[-1],
            periods=forecast_days + 1,
            freq="B"
        )[1:]

        future_df = pd.DataFrame({
            "date": future_dates,
            "predicted_return": future_returns,
            "previous_price": previous_prices,
            "predicted_price": future_prices,
        })

        future_path = f"{ticker_dir}/future_xgb_{ticker.replace('^', '')}.csv"
        future_df.to_csv(future_path, index=False)
        mlflow.log_artifact(future_path)

        model_path = f"{ticker_dir}/xgb_model_{ticker.replace('^', '')}.json"
        model.save_model(model_path)
        mlflow.log_artifact(model_path)

        # Register model formally in MLFlow Model Registry
        model_name = f"xgboost_model_{ticker.replace('^', '')}"
        mlflow.xgboost.log_model(
            model,
            artifact_path="model",
            registered_model_name=model_name
        )

        print(f"Last known price: {previous_prices[-1]:.2f}")
        print(f"Forecast in {forecast_days} days: {future_prices[-1]:.2f}")
        print("Run logged to MLflow")

        return model, future_df


if __name__ == "__main__":
    train_xgboost(
        ticker="^GSPC",
        forecast_days=30
    )

        



